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

# Initialize signal processors for pipeline orchestrator
from src.processors import (
    MempoolProcessor,
    ExchangeProcessor,
    MinerProcessor,
    WhaleProcessor,
    TreasuryProcessor,
    PredictiveAnalyticsModule
)
from src.processors.base_processor import ProcessorConfig
from src.pipeline_orchestrator import PipelineOrchestrator
from src.signal_persistence import SignalPersistenceModule
from src.monitoring import MonitoringModule

# Create processor configuration
processor_config = ProcessorConfig(
    enabled=True,
    confidence_threshold=0.5,  # Lower threshold for predictive signals
    time_window='24h'
)

# Initialize all signal processors including predictive analytics
signal_processors = [
    MempoolProcessor(processor_config),
    ExchangeProcessor(processor_config),
    MinerProcessor(processor_config),
    WhaleProcessor(processor_config),
    TreasuryProcessor(processor_config),
    PredictiveAnalyticsModule(processor_config)  # Predictive analytics integrated
]

# Initialize monitoring and persistence modules
monitoring_module = MonitoringModule(
    project_id=os.getenv('GCP_PROJECT_ID', 'utxoiq-dev'),
    enabled=os.getenv('MONITORING_ENABLED', 'false').lower() == 'true'
)

signal_persistence = SignalPersistenceModule(
    bigquery_client=bq_client,
    project_id=os.getenv('GCP_PROJECT_ID', 'utxoiq-dev')
)

# Initialize pipeline orchestrator
pipeline_orchestrator = PipelineOrchestrator(
    signal_processors=signal_processors,
    signal_persistence=signal_persistence,
    monitoring_module=monitoring_module
)

logger.info(f"Pipeline orchestrator initialized with {len(signal_processors)} processors")

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
        
        # Create and start monitor with pipeline orchestrator
        monitor = BlockMonitor(
            rpc_client=rpc_client,
            block_processor=block_processor,
            bigquery_adapter=bq_adapter,
            pipeline_orchestrator=pipeline_orchestrator,
            poll_interval=int(os.getenv('POLL_INTERVAL', '30')),
            mempool_api_url=os.getenv('MEMPOOL_API_URL', 'https://mempool.space/api')
        )
        monitor.start()
        logger.info("Block monitor started successfully with signal generation pipeline")
        
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


@app.post("/process/signals")
async def process_signals(block_data: Dict):
    """
    Process a block through the signal generation pipeline.
    
    This endpoint runs all signal processors (including predictive analytics)
    on the provided block data and persists signals to BigQuery.
    
    Args:
        block_data: Block data with optional historical context
        
    Returns:
        Pipeline processing result with generated signals
    """
    try:
        from src.models import BlockData
        
        # Extract block info
        block = BlockData(
            block_hash=block_data.get('hash', ''),
            height=block_data.get('height', 0),
            timestamp=datetime.fromisoformat(block_data['timestamp']) if 'timestamp' in block_data else datetime.utcnow(),
            size=block_data.get('size', 0),
            tx_count=block_data.get('tx_count', 0),
            fees_total=block_data.get('fees_total', 0.0)
        )
        
        # Extract historical data if provided
        historical_data = block_data.get('historical_data', {})
        
        # Process through pipeline
        result = await pipeline_orchestrator.process_new_block(
            block=block,
            historical_data=historical_data
        )
        
        return {
            "status": "success" if result.success else "failed",
            "correlation_id": result.correlation_id,
            "block_height": result.block_height,
            "signals_generated": len(result.signals),
            "signal_types": [s.type.value for s in result.signals],
            "predictive_signals": sum(1 for s in result.signals if s.is_predictive),
            "timing_metrics": result.timing_metrics,
            "error": result.error
        }
        
    except Exception as e:
        logger.error(f"Signal processing failed: {str(e)}", exc_info=True)
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
            "custom_dataset_stats": stats,
            "pipeline": {
                "processors": len(signal_processors),
                "enabled_processors": sum(1 for p in signal_processors if p.enabled),
                "processor_types": [p.__class__.__name__ for p in signal_processors if p.enabled]
            }
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
