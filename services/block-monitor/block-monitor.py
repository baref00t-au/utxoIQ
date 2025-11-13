"""
Bitcoin Block Monitor Service with Tor support.
Continuously monitors Bitcoin Core via Tor and sends blocks to feature-engine.
"""

import os
import sys
import time
import logging
import requests
import json
from decimal import Decimal
from datetime import datetime
from bitcoinrpc.authproxy import AuthServiceProxy
from fastapi import FastAPI
from threading import Thread
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app for health checks
app = FastAPI(title="Block Monitor")


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from Bitcoin RPC."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class BlockMonitor:
    """Monitor Bitcoin Core for new blocks via Tor with mempool.space fallback."""
    
    def __init__(
        self,
        rpc_url: str,
        feature_engine_url: str,
        poll_interval: int = 10,
        use_tor: bool = True,
        mempool_api_url: str = "https://mempool.space/api"
    ):
        """
        Initialize block monitor.
        
        Args:
            rpc_url: Bitcoin Core RPC URL (can be .onion address)
            feature_engine_url: Feature engine service URL
            poll_interval: Seconds between checks (default: 10)
            use_tor: Use Tor SOCKS proxy (default: True)
            mempool_api_url: mempool.space API URL for fallback
        """
        self.feature_engine_url = feature_engine_url.rstrip('/')
        self.poll_interval = poll_interval
        self.last_processed_height = None
        self.use_tor = use_tor
        self.running = False
        self.mempool_api_url = mempool_api_url.rstrip('/')
        self.consecutive_failures = 0
        self.max_failures = 3
        self.using_fallback = False
        
        # Configure RPC client with Tor proxy if needed
        if use_tor and '.onion' in rpc_url:
            # Use Tor SOCKS proxy for .onion addresses
            import socks
            import socket
            
            # Configure SOCKS proxy
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            socket.socket = socks.socksocket
            
            logger.info("Using Tor SOCKS proxy for Bitcoin RPC")
        
        self.rpc = AuthServiceProxy(rpc_url)
        
        # Configure requests session with Tor proxy for feature-engine calls
        self.session = requests.Session()
        if use_tor:
            self.session.proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }
        
        # Separate session for mempool.space (no Tor proxy)
        self.mempool_session = requests.Session()
    
    def get_current_height(self) -> int:
        """Get current blockchain height with fallback to mempool.space."""
        try:
            height = self.rpc.getblockcount()
            self.consecutive_failures = 0
            if self.using_fallback:
                logger.info("✅ Umbrel connection restored, switching back from fallback")
                self.using_fallback = False
            return height
        except Exception as e:
            self.consecutive_failures += 1
            logger.warning(f"⚠️  Umbrel RPC failed ({self.consecutive_failures}/{self.max_failures}): {e}")
            
            if self.consecutive_failures >= self.max_failures:
                if not self.using_fallback:
                    logger.warning("🔄 Switching to mempool.space fallback")
                    self.using_fallback = True
                
                # Fallback to mempool.space
                try:
                    response = self.mempool_session.get(
                        f"{self.mempool_api_url}/blocks/tip/height",
                        timeout=10
                    )
                    response.raise_for_status()
                    return int(response.text)
                except Exception as fallback_error:
                    logger.error(f"❌ mempool.space fallback also failed: {fallback_error}")
                    raise
            else:
                raise
    
    def get_block_data(self, height: int) -> dict:
        """
        Get full block data including transactions with fallback to mempool.space.
        
        Args:
            height: Block height
            
        Returns:
            Block data with transactions
        """
        try:
            block_hash = self.rpc.getblockhash(height)
            # verbosity=2 includes full transaction data
            block_data = self.rpc.getblock(block_hash, 2)
            return block_data
        except Exception as e:
            if self.using_fallback:
                logger.info(f"🔄 Fetching block {height} from mempool.space")
                # Get block hash from mempool.space
                response = self.mempool_session.get(
                    f"{self.mempool_api_url}/block-height/{height}",
                    timeout=10
                )
                response.raise_for_status()
                block_hash = response.text
                
                # Get full block data
                response = self.mempool_session.get(
                    f"{self.mempool_api_url}/block/{block_hash}",
                    timeout=10
                )
                response.raise_for_status()
                block_data = response.json()
                
                # Note: mempool.space doesn't include full tx data by default
                # We'll need to fetch transactions separately if needed
                logger.warning("⚠️  Using mempool.space data (limited transaction details)")
                return block_data
            else:
                raise
    
    def send_to_feature_engine(self, block_data: dict) -> bool:
        """
        Send block data to feature-engine service.
        
        Args:
            block_data: Block data from Bitcoin Core
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to JSON string with Decimal handling
            json_data = json.dumps(block_data, cls=DecimalEncoder)
            
            response = self.session.post(
                f"{self.feature_engine_url}/ingest/block",
                data=json_data,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Block {block_data['height']} ingested: {result['status']}")
            
            if result['status'] == 'skipped':
                logger.info(f"   Reason: {result['reason']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send block {block_data['height']}: {e}")
            return False
    
    def start(self):
        """Start monitoring for new blocks."""
        logger.info("=" * 60)
        logger.info("Bitcoin Block Monitor (Cloud Run + Tor)")
        logger.info("=" * 60)
        logger.info(f"Feature Engine: {self.feature_engine_url}")
        logger.info(f"Poll interval: {self.poll_interval}s")
        logger.info(f"Using Tor: {self.use_tor}")
        logger.info("=" * 60)
        
        self.running = True
        
        try:
            # Get initial state
            current_height = self.get_current_height()
            self.last_processed_height = current_height
            logger.info(f"Starting from current tip: {current_height}")
            logger.info("Monitoring for new blocks...")
            logger.info("")
            
            # Main loop
            while self.running:
                try:
                    current_height = self.get_current_height()
                    
                    # Process any new blocks
                    while self.last_processed_height < current_height and self.running:
                        next_height = self.last_processed_height + 1
                        
                        logger.info(f"📦 New block detected: {next_height}")
                        
                        # Get block data
                        block_data = self.get_block_data(next_height)
                        
                        # Send to feature-engine
                        success = self.send_to_feature_engine(block_data)
                        
                        if success:
                            self.last_processed_height = next_height
                            logger.info(f"   Transactions: {len(block_data.get('tx', []))}")
                            logger.info(f"   Timestamp: {datetime.fromtimestamp(block_data['time'])}")
                            logger.info("")
                        else:
                            logger.warning(f"   Retrying in {self.poll_interval}s...")
                            break
                    
                    # Wait before next check
                    time.sleep(self.poll_interval)
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {e}", exc_info=True)
                    time.sleep(self.poll_interval)
        
        except Exception as e:
            logger.error(f"Failed to start monitor: {e}", exc_info=True)
            raise
    
    def stop(self):
        """Stop the monitor."""
        logger.info("Stopping block monitor...")
        self.running = False


# Global monitor instance
monitor = None


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {
        "status": "healthy",
        "service": "block-monitor",
        "timestamp": datetime.utcnow().isoformat(),
        "monitoring": monitor.running if monitor else False,
        "last_processed_height": monitor.last_processed_height if monitor else None
    }


@app.get("/status")
async def get_status():
    """Get monitor status."""
    if not monitor:
        return {"status": "not_started"}
    
    return {
        "status": "running" if monitor.running else "stopped",
        "last_processed_height": monitor.last_processed_height,
        "poll_interval": monitor.poll_interval,
        "using_tor": monitor.use_tor,
        "using_fallback": monitor.using_fallback,
        "consecutive_failures": monitor.consecutive_failures,
        "data_source": "mempool.space" if monitor.using_fallback else "umbrel"
    }


def run_monitor():
    """Run the block monitor in a separate thread."""
    global monitor
    
    # Get configuration from environment
    rpc_url = os.getenv('BITCOIN_RPC_URL')
    feature_engine_url = os.getenv('FEATURE_ENGINE_URL', 'https://utxoiq-ingestion-544291059247.us-central1.run.app')
    poll_interval = int(os.getenv('POLL_INTERVAL', '30'))
    mempool_api_url = os.getenv('MEMPOOL_API_URL', 'https://mempool.space/api')
    
    if not rpc_url:
        logger.error("BITCOIN_RPC_URL environment variable not set")
        sys.exit(1)
    
    # Create and start monitor
    monitor = BlockMonitor(
        rpc_url=rpc_url,
        feature_engine_url=feature_engine_url,
        poll_interval=poll_interval,
        use_tor=True,
        mempool_api_url=mempool_api_url
    )
    
    monitor.start()


def main():
    """Entry point."""
    # Start monitor in background thread
    monitor_thread = Thread(target=run_monitor, daemon=True)
    monitor_thread.start()
    
    # Start FastAPI server for health checks
    port = int(os.getenv('PORT', '8080'))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == '__main__':
    main()
