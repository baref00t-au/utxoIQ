"""
utxoIQ Ingestion Service - Bitcoin blockchain data ingestion and processing.
"""

from fastapi import FastAPI, HTTPException
from datetime import datetime
import logging
import os
from typing import Dict, Optional

from src.adapters.bigquery_adapter import BigQueryAdapter
from src.processors.bitcoin_block_processor import BitcoinBlockProcessor
from src.monitor.block_monitor import BlockMonitor
from src.entity_identification import EntityIdentificationModule
from google.cloud import bigquery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="utxoIQ Ingestion Service",
    description="Bitcoin blockchain data ingestion and real-time monitoring",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on application startup."""
    logger.info("Starting application background tasks")
    
    # Start entity cache background reload
    entity_module.start_background_reload()
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up background tasks on application shutdown."""
    logger.info("Shutting down application background tasks")
    
    # Stop entity cache background reload
    await entity_module.stop_background_reload()
    
    logger.info("Application shutdown complete")

# Initialize adapters
bq_adapter = BigQueryAdapter()
block_processor = BitcoinBlockProcessor()

# Initialize entity identification module
bq_client = bigquery.Client()
entity_module = EntityIdentificationModule(bigquery_client=bq_client)

# Initialize block monitor (optional - only if Bitcoin RPC is configured)
monitor: Optional[BlockMonitor] = None
bitcoin_rpc_url = os.getenv('BITCOIN_RPC_URL')

if bitcoin_rpc_url:
    try:
        from bitcoinrpc.authproxy import AuthServiceProxy
        from src.utils.tor_rpc import TorAuthServiceProxy
        
        # Use Tor-enabled client if .onion address
        if '.onion' in bitcoin_rpc_url:
            logger.info("Using Tor SOCKS proxy for Bitcoin RPC")
            rpc_client = TorAuthServiceProxy(bitcoin_rpc_url)
        else:
            rpc_client = AuthServiceProxy(bitcoin_rpc_url)
        
        # Test connection
        block_count = rpc_client.getblockcount()
        logger.info(f"Connected to Bitcoin Core (height: {block_count})")
        
        # Create and start monitor
        monitor = BlockMonitor(
            rpc_client=rpc_client,
            block_processor=block_processor,
            bigquery_adapter=bq_adapter,
            poll_interval=int(os.getenv('POLL_INTERVAL', '30')),
            mempool_api_url=os.getenv('MEMPOOL_API_URL', 'https://mempool.space/api')
        )
        monitor.start()
        logger.info("Block monitor started successfully")
        
    except Exception as e:
        logger.warning(f"Could not start block monitor: {e}")
        logger.info("Service will run in API-only mode")
else:
    logger.info("BITCOIN_RPC_URL not configured - running in API-only mode")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "utxoiq-ingestion",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/ingest/block")
async def ingest_block(block_data: Dict):
    """
    Ingest a Bitcoin block into BigQuery.
    
    Args:
        block_data: Raw block data from Bitcoin Core RPC
        
    Returns:
        Ingestion status
    """
    try:
        # Process block
        processed_block = block_processor.process_block(block_data)
        
        # Check if block should be ingested
        if not bq_adapter.should_ingest_block(processed_block['timestamp']):
            return {
                "status": "skipped",
                "reason": "Block is older than 24 hours",
                "block_height": processed_block['number'],
                "block_timestamp": processed_block['timestamp'].isoformat()
            }
        
        # Insert block
        bq_adapter.insert_block(processed_block)
        
        # Process and insert transactions if present (with nested inputs/outputs)
        if 'tx' in block_data:
            transactions = []
            
            for tx_data in block_data['tx']:
                # Process transaction with nested inputs/outputs
                tx = block_processor.process_transaction(
                    tx_data,
                    processed_block['hash'],
                    processed_block['number'],
                    processed_block['timestamp']
                )
                transactions.append(tx)
            
            # Batch insert transactions (inputs/outputs are nested)
            bq_adapter.insert_transactions(transactions)
        
        return {
            "status": "success",
            "block_height": processed_block['number'],
            "block_hash": processed_block['hash'],
            "block_timestamp": processed_block['timestamp'].isoformat(),
            "transaction_count": processed_block['transaction_count']
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest block: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cleanup")
async def cleanup_old_data(hours: int = 2):
    """
    Clean up data older than specified hours.
    
    Args:
        hours: Delete data older than this many hours (default: 2 hours)
        
    Returns:
        Cleanup statistics
    """
    try:
        results = bq_adapter.cleanup_old_data(hours)
        
        return {
            "status": "success",
            "deleted": results,
            "cutoff_hours": hours,
            "warning": "Cleanup deleted more than 200 blocks" if results.get('blocks', 0) > 200 else None
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """
    Get ingestion status.
    
    Returns:
        Current status including latest block height and dataset stats
    """
    try:
        latest_height = bq_adapter.get_latest_block_height()
        stats = bq_adapter.get_dataset_stats()
        
        status = {
            "status": "operational",
            "latest_block_height": latest_height,
            "dataset": f"{bq_adapter.project_id}.{bq_adapter.dataset_id}",
            "realtime_window_hours": bq_adapter.realtime_hours,
            "custom_dataset_stats": stats
        }
        
        # Add monitor status if available
        if monitor:
            status["monitor"] = monitor.get_status()
        else:
            status["monitor"] = {"enabled": False, "reason": "BITCOIN_RPC_URL not configured"}
        
        return status
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
