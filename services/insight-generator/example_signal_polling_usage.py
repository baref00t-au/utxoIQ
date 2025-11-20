"""
Example usage of Signal Polling Module

Demonstrates how to use the SignalPollingModule to poll for unprocessed signals
and mark them as processed after insight generation.
"""

import asyncio
import logging
from google.cloud import bigquery
from src.signal_polling import SignalPollingModule

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_polling_workflow():
    """
    Example workflow showing how to:
    1. Poll for unprocessed signals
    2. Process signals (generate insights)
    3. Mark signals as processed
    """
    
    # Initialize BigQuery client
    project_id = "utxoiq-dev"
    bq_client = bigquery.Client(project=project_id)
    
    # Initialize Signal Polling Module
    polling_module = SignalPollingModule(
        bigquery_client=bq_client,
        project_id=project_id,
        dataset_id="intel",
        confidence_threshold=0.7
    )
    
    logger.info("=" * 60)
    logger.info("Signal Polling Example")
    logger.info("=" * 60)
    
    # Step 1: Check for stale signals (monitoring)
    stale_signals = await polling_module.get_stale_signals(max_age_hours=1)
    if stale_signals:
        logger.warning(f"Found {len(stale_signals)} stale signals!")
        for signal in stale_signals[:3]:  # Show first 3
            logger.warning(
                f"  - Signal {signal['signal_id']}: "
                f"{signal['signal_type']} (age: {signal['age_hours']} hours)"
            )
    
    # Step 2: Get count of unprocessed signals
    unprocessed_count = await polling_module.get_unprocessed_signal_count()
    logger.info(f"Unprocessed signals: {unprocessed_count}")
    
    # Step 3: Poll for unprocessed signals
    signal_groups = await polling_module.poll_unprocessed_signals(limit=50)
    
    if not signal_groups:
        logger.info("No signals to process")
        return
    
    logger.info(f"Found {len(signal_groups)} signal groups to process")
    
    # Step 4: Process each group
    for group in signal_groups:
        logger.info(
            f"\nProcessing group: {group.signal_type} "
            f"(block {group.block_height}, {len(group.signals)} signals)"
        )
        
        # Simulate insight generation for each signal in the group
        signal_ids_to_mark = []
        
        for signal in group.signals:
            logger.info(
                f"  - Signal {signal['signal_id']}: "
                f"confidence={signal['confidence']:.2f}"
            )
            
            # TODO: Generate insight from signal
            # insight = await generate_insight(signal)
            # await persist_insight(insight)
            
            # Collect signal IDs for batch marking
            signal_ids_to_mark.append(signal['signal_id'])
        
        # Step 5: Mark signals as processed (batch operation)
        if signal_ids_to_mark:
            marked_count = await polling_module.mark_signals_processed_batch(
                signal_ids_to_mark
            )
            logger.info(f"✓ Marked {marked_count} signals as processed")
    
    logger.info("\n" + "=" * 60)
    logger.info("Polling cycle complete")
    logger.info("=" * 60)


async def example_continuous_polling():
    """
    Example of continuous polling loop (production pattern).
    """
    
    # Initialize
    project_id = "utxoiq-dev"
    bq_client = bigquery.Client(project=project_id)
    
    polling_module = SignalPollingModule(
        bigquery_client=bq_client,
        project_id=project_id,
        dataset_id="intel",
        confidence_threshold=0.7
    )
    
    logger.info("Starting continuous polling (Ctrl+C to stop)")
    
    try:
        while True:
            # Poll for signals
            signal_groups = await polling_module.poll_unprocessed_signals()
            
            if signal_groups:
                logger.info(f"Processing {len(signal_groups)} signal groups...")
                
                for group in signal_groups:
                    # Process signals and generate insights
                    # (implementation would go here)
                    
                    # Mark as processed
                    signal_ids = [s['signal_id'] for s in group.signals]
                    await polling_module.mark_signals_processed_batch(signal_ids)
            
            # Wait before next poll
            await asyncio.sleep(polling_module.poll_interval)
            
    except KeyboardInterrupt:
        logger.info("Polling stopped by user")


async def example_single_signal_processing():
    """
    Example of processing a single signal.
    """
    
    # Initialize
    project_id = "utxoiq-dev"
    bq_client = bigquery.Client(project=project_id)
    
    polling_module = SignalPollingModule(
        bigquery_client=bq_client,
        project_id=project_id,
        dataset_id="intel"
    )
    
    # Poll for one signal
    signal_groups = await polling_module.poll_unprocessed_signals(limit=1)
    
    if signal_groups and signal_groups[0].signals:
        signal = signal_groups[0].signals[0]
        signal_id = signal['signal_id']
        
        logger.info(f"Processing signal: {signal_id}")
        
        # Generate insight
        # insight = await generate_insight(signal)
        
        # Mark as processed
        success = await polling_module.mark_signal_processed(signal_id)
        
        if success:
            logger.info(f"✓ Signal {signal_id} processed successfully")
        else:
            logger.error(f"✗ Failed to mark signal {signal_id} as processed")


if __name__ == "__main__":
    # Run the example workflow
    asyncio.run(example_polling_workflow())
    
    # Uncomment to run continuous polling:
    # asyncio.run(example_continuous_polling())
    
    # Uncomment to run single signal processing:
    # asyncio.run(example_single_signal_processing())
