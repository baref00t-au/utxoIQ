"""
Example usage of Historical Backfill Module.

This script demonstrates how to use the HistoricalBackfillModule to backfill
historical signals for past blocks.
"""

import asyncio
import logging
from datetime import date, timedelta
from google.cloud import bigquery

from src.historical_backfill import HistoricalBackfillModule
from src.signal_persistence import SignalPersistenceModule
from src.processors.mempool_processor import MempoolProcessor
from src.processors.exchange_processor import ExchangeProcessor
from src.processors.miner_processor import MinerProcessor
from src.processors.whale_processor import WhaleProcessor
from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run historical backfill example."""
    
    # Initialize BigQuery client
    bigquery_client = bigquery.Client(project=settings.gcp_project_id)
    
    # Initialize signal persistence module
    signal_persistence = SignalPersistenceModule(
        bigquery_client=bigquery_client,
        project_id=settings.gcp_project_id,
        dataset_id=settings.bigquery_dataset_intel,
        table_name="signals"
    )
    
    # Initialize signal processors
    # Note: You'll need to initialize these with proper dependencies
    # This is a simplified example
    signal_processors = [
        # MempoolProcessor(...),
        # ExchangeProcessor(...),
        # MinerProcessor(...),
        # WhaleProcessor(...),
    ]
    
    # Initialize historical backfill module
    backfill_module = HistoricalBackfillModule(
        bigquery_client=bigquery_client,
        signal_processors=signal_processors,
        signal_persistence=signal_persistence,
        rate_limit_blocks_per_minute=100  # Adjust as needed
    )
    
    # Example 1: Backfill last 7 days
    logger.info("Example 1: Backfill last 7 days")
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    result = await backfill_module.backfill_date_range(
        start_date=start_date,
        end_date=end_date
    )
    
    logger.info(f"Backfill result: {result}")
    logger.info(f"Processed {result.blocks_processed} blocks")
    logger.info(f"Generated {result.signals_generated} signals")
    logger.info(f"Duration: {result.duration_seconds:.2f} seconds")
    logger.info(f"Errors: {len(result.errors)}")
    
    # Example 2: Selective backfill (only mempool and exchange signals)
    logger.info("\nExample 2: Selective backfill (mempool and exchange only)")
    
    result = await backfill_module.backfill_date_range(
        start_date=start_date,
        end_date=end_date,
        signal_types=["mempool", "exchange"]
    )
    
    logger.info(f"Selective backfill result: {result}")
    
    # Example 3: Backfill specific date range
    logger.info("\nExample 3: Backfill specific date range")
    
    result = await backfill_module.backfill_date_range(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31)
    )
    
    logger.info(f"Date range backfill result: {result}")
    
    # Example 4: Custom rate limit
    logger.info("\nExample 4: Custom rate limit (50 blocks/min)")
    
    backfill_module_slow = HistoricalBackfillModule(
        bigquery_client=bigquery_client,
        signal_processors=signal_processors,
        signal_persistence=signal_persistence,
        rate_limit_blocks_per_minute=50  # Slower rate
    )
    
    result = await backfill_module_slow.backfill_date_range(
        start_date=start_date,
        end_date=end_date
    )
    
    logger.info(f"Slow backfill result: {result}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
