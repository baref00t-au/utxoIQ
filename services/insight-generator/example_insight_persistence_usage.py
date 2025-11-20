"""
Example usage of InsightPersistenceModule.

This script demonstrates how to use the Insight Persistence Module
to write insights to BigQuery and handle persistence operations.

Requirements: 4.1, 4.3, 4.4, 4.5
"""

import asyncio
import logging
from datetime import datetime
from google.cloud import bigquery

from src.insight_persistence import InsightPersistenceModule, PersistenceResult
from src.insight_generation import Insight, Evidence


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_basic_persistence():
    """Example: Basic insight persistence"""
    print("\n" + "="*60)
    print("Example 1: Basic Insight Persistence")
    print("="*60)
    
    # Initialize BigQuery client
    bq_client = bigquery.Client(project="utxoiq-dev")
    
    # Initialize persistence module
    persistence = InsightPersistenceModule(
        bigquery_client=bq_client,
        project_id="utxoiq-dev",
        dataset_id="intel"
    )
    
    # Create a sample insight (mempool signal)
    insight = Insight(
        insight_id="550e8400-e29b-41d4-a716-446655440000",
        signal_id="123e4567-e89b-12d3-a456-426614174000",
        category="mempool",
        headline="Bitcoin Fees Spike 25% as Mempool Congestion Increases",
        summary="Transaction fees have surged to 50.5 sat/vB, marking a 25% increase compared to the previous hour. The mempool has grown to 120.5 MB with over 15,000 pending transactions, indicating significant network congestion.",
        confidence=0.85,
        evidence=Evidence(
            block_heights=[820000],
            transaction_ids=["abc123def456...", "789ghi012jkl..."]
        ),
        chart_url=None,  # Will be populated later by chart-renderer
        created_at=datetime.utcnow()
    )
    
    print(f"\n📝 Persisting insight:")
    print(f"   Insight ID: {insight.insight_id}")
    print(f"   Signal ID: {insight.signal_id}")
    print(f"   Category: {insight.category}")
    print(f"   Headline: {insight.headline}")
    print(f"   Confidence: {insight.confidence}")
    
    # Persist the insight
    result = await persistence.persist_insight(
        insight=insight,
        correlation_id="example-req-001"
    )
    
    if result.success:
        print(f"\n✅ Success! Insight persisted: {result.insight_id}")
        
        # Verify by retrieving the insight
        retrieved = await persistence.get_insight_by_id(result.insight_id)
        if retrieved:
            print(f"✅ Verified: Insight retrieved from BigQuery")
            print(f"   Headline: {retrieved['headline']}")
            print(f"   Chart URL: {retrieved['chart_url']} (null as expected)")
    else:
        print(f"\n❌ Failed: {result.error}")


async def example_batch_persistence():
    """Example: Batch insight persistence"""
    print("\n" + "="*60)
    print("Example 2: Batch Insight Persistence")
    print("="*60)
    
    # Initialize
    bq_client = bigquery.Client(project="utxoiq-dev")
    persistence = InsightPersistenceModule(bq_client)
    
    # Create multiple insights
    insights = [
        Insight(
            insight_id=f"insight-{i:03d}",
            signal_id=f"signal-{i:03d}",
            category="exchange",
            headline=f"Exchange Flow #{i}: Significant Activity Detected",
            summary=f"Exchange flow analysis shows notable activity in block {820000 + i}.",
            confidence=0.75 + (i * 0.05),
            evidence=Evidence(
                block_heights=[820000 + i],
                transaction_ids=[f"tx-{i:03d}"]
            )
        )
        for i in range(5)
    ]
    
    print(f"\n📝 Persisting {len(insights)} insights in batch...")
    
    # Persist batch
    results = await persistence.persist_insights_batch(
        insights=insights,
        correlation_id="example-req-002"
    )
    
    print(f"\n✅ Succeeded: {results['success_count']}")
    print(f"❌ Failed: {results['failure_count']}")
    print(f"📊 Insight IDs: {results['insight_ids'][:3]}...")


async def example_error_handling():
    """Example: Error handling and retry mechanism"""
    print("\n" + "="*60)
    print("Example 3: Error Handling and Retry")
    print("="*60)
    
    # Initialize
    bq_client = bigquery.Client(project="utxoiq-dev")
    persistence = InsightPersistenceModule(bq_client)
    
    # Create an insight with invalid data (to trigger error)
    # Note: In real usage, this would be caught by validation
    insight = Insight(
        insight_id="error-test-001",
        signal_id="signal-error-001",
        category="mempool",
        headline="Test Error Handling",
        summary="This insight is for testing error handling.",
        confidence=0.80,
        evidence=Evidence(
            block_heights=[820000],
            transaction_ids=[]
        )
    )
    
    print(f"\n📝 Attempting to persist insight (may fail)...")
    
    result = await persistence.persist_insight(
        insight=insight,
        correlation_id="example-req-003"
    )
    
    if result.success:
        print(f"✅ Success: {result.insight_id}")
    else:
        print(f"❌ Failed: {result.error}")
        print(f"🔄 Signal {insight.signal_id} marked as unprocessed for retry")


async def example_query_utilities():
    """Example: Query utilities for verification"""
    print("\n" + "="*60)
    print("Example 4: Query Utilities")
    print("="*60)
    
    # Initialize
    bq_client = bigquery.Client(project="utxoiq-dev")
    persistence = InsightPersistenceModule(bq_client)
    
    # First, persist an insight
    insight = Insight(
        insight_id="query-test-001",
        signal_id="signal-query-001",
        category="whale",
        headline="Large Bitcoin Holder Moves 1,500 BTC",
        summary="A whale address with over 10,000 BTC balance has moved 1,500 BTC in a single transaction.",
        confidence=0.90,
        evidence=Evidence(
            block_heights=[820000],
            transaction_ids=["whale-tx-001"]
        )
    )
    
    print(f"\n📝 Persisting test insight...")
    result = await persistence.persist_insight(insight)
    
    if result.success:
        print(f"✅ Persisted: {result.insight_id}")
        
        # Query by insight ID
        print(f"\n🔍 Querying by insight ID...")
        retrieved = await persistence.get_insight_by_id(result.insight_id)
        if retrieved:
            print(f"✅ Found insight:")
            print(f"   Headline: {retrieved['headline']}")
            print(f"   Category: {retrieved['category']}")
            print(f"   Confidence: {retrieved['confidence']}")
        
        # Query by signal ID
        print(f"\n🔍 Querying by signal ID...")
        insights = await persistence.get_insights_by_signal_id(insight.signal_id)
        print(f"✅ Found {len(insights)} insight(s) for signal {insight.signal_id}")


async def example_complete_workflow():
    """Example: Complete workflow from signal to persisted insight"""
    print("\n" + "="*60)
    print("Example 5: Complete Workflow")
    print("="*60)
    
    # Initialize
    bq_client = bigquery.Client(project="utxoiq-dev")
    persistence = InsightPersistenceModule(bq_client)
    
    # Simulate a signal from BigQuery
    signal = {
        "signal_id": "workflow-signal-001",
        "signal_type": "treasury",
        "block_height": 820000,
        "confidence": 0.88,
        "metadata": {
            "entity_name": "MicroStrategy",
            "company_ticker": "MSTR",
            "flow_type": "accumulation",
            "amount_btc": 500.0,
            "known_holdings_btc": 152800,
            "holdings_change_pct": 0.33
        },
        "created_at": datetime.utcnow()
    }
    
    print(f"\n📊 Processing signal:")
    print(f"   Signal ID: {signal['signal_id']}")
    print(f"   Type: {signal['signal_type']}")
    print(f"   Confidence: {signal['confidence']}")
    
    # In real workflow, InsightGenerationModule would create the insight
    # Here we simulate it
    insight = Insight(
        insight_id="workflow-insight-001",
        signal_id=signal["signal_id"],
        category=signal["signal_type"],
        headline="MicroStrategy Adds 500 BTC to Treasury Holdings",
        summary="MicroStrategy (MSTR) has accumulated an additional 500 BTC, increasing their total holdings by 0.33%. This marks continued institutional adoption and long-term Bitcoin accumulation strategy.",
        confidence=signal["confidence"],
        evidence=Evidence(
            block_heights=[signal["block_height"]],
            transaction_ids=[]
        )
    )
    
    print(f"\n💡 Generated insight:")
    print(f"   Insight ID: {insight.insight_id}")
    print(f"   Headline: {insight.headline}")
    
    # Persist the insight
    print(f"\n💾 Persisting insight...")
    result = await persistence.persist_insight(
        insight=insight,
        correlation_id="workflow-req-001"
    )
    
    if result.success:
        print(f"✅ Complete! Insight persisted: {result.insight_id}")
        print(f"📈 Ready for chart-renderer to populate chart_url")
        print(f"🌐 Ready for web-api to serve to users")
    else:
        print(f"❌ Failed: {result.error}")
        print(f"🔄 Signal marked for retry")


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Insight Persistence Module - Example Usage")
    print("="*60)
    
    try:
        # Run examples
        await example_basic_persistence()
        await example_batch_persistence()
        await example_error_handling()
        await example_query_utilities()
        await example_complete_workflow()
        
        print("\n" + "="*60)
        print("✅ All examples completed!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
