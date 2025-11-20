"""
Example usage of InsightGenerationModule

This script demonstrates how to use the InsightGenerationModule
to generate insights from signals.
"""

import asyncio
import uuid
from datetime import datetime

from src.insight_generation import InsightGenerationModule
from src.ai_provider import AIProviderFactory


async def main():
    """Demonstrate InsightGenerationModule usage"""
    
    print("=" * 60)
    print("InsightGenerationModule Example Usage")
    print("=" * 60)
    
    # Step 1: Create AI provider
    # In production, this would load from environment variables
    print("\n1. Creating AI provider...")
    
    # For this example, we'll use a mock configuration
    # In production, use: provider = get_configured_provider()
    try:
        provider = AIProviderFactory.create_provider(
            "vertex_ai",
            config={
                "project_id": "utxoiq-dev",
                "location": "us-central1",
                "model": "gemini-pro"
            }
        )
        print(f"   ✓ Created provider: {provider.__class__.__name__}")
    except Exception as e:
        print(f"   ✗ Failed to create provider: {e}")
        print("   Note: This is expected if Vertex AI credentials are not configured")
        print("   In production, ensure AI_PROVIDER env var is set")
        return
    
    # Step 2: Initialize InsightGenerationModule
    print("\n2. Initializing InsightGenerationModule...")
    module = InsightGenerationModule(provider)
    print(f"   ✓ Module initialized with {len(module.PROMPT_TEMPLATES)} prompt templates")
    
    # Step 3: Create sample signals
    print("\n3. Creating sample signals...")
    
    mempool_signal = {
        "signal_id": str(uuid.uuid4()),
        "signal_type": "mempool",
        "block_height": 800000,
        "confidence": 0.85,
        "metadata": {
            "fee_rate_median": 50.5,
            "fee_rate_change_pct": 25.3,
            "mempool_size_mb": 120.5,
            "tx_count": 15000,
            "tx_ids": ["abc123", "def456", "ghi789"]
        },
        "created_at": datetime.utcnow()
    }
    
    exchange_signal = {
        "signal_id": str(uuid.uuid4()),
        "signal_type": "exchange",
        "block_height": 800001,
        "confidence": 0.78,
        "metadata": {
            "entity_id": "coinbase_001",
            "entity_name": "Coinbase",
            "flow_type": "outflow",
            "amount_btc": 1250.5,
            "tx_count": 45,
            "addresses": ["bc1q...", "3FZbgi..."],
            "transaction_ids": ["tx001", "tx002"]
        },
        "created_at": datetime.utcnow()
    }
    
    treasury_signal = {
        "signal_id": str(uuid.uuid4()),
        "signal_type": "treasury",
        "block_height": 800002,
        "confidence": 0.92,
        "metadata": {
            "entity_id": "microstrategy_001",
            "entity_name": "MicroStrategy",
            "company_ticker": "MSTR",
            "flow_type": "accumulation",
            "amount_btc": 500.0,
            "known_holdings_btc": 152800,
            "holdings_change_pct": 0.33,
            "txids": ["tx003"]
        },
        "created_at": datetime.utcnow()
    }
    
    signals = [mempool_signal, exchange_signal, treasury_signal]
    print(f"   ✓ Created {len(signals)} sample signals")
    
    # Step 4: Generate insights
    print("\n4. Generating insights...")
    
    for i, signal in enumerate(signals, 1):
        print(f"\n   Signal {i}: {signal['signal_type']}")
        print(f"   - Signal ID: {signal['signal_id']}")
        print(f"   - Block Height: {signal['block_height']}")
        print(f"   - Confidence: {signal['confidence']}")
        
        try:
            insight = await module.generate_insight(signal)
            
            if insight:
                print(f"   ✓ Generated insight:")
                print(f"     - Insight ID: {insight.insight_id}")
                print(f"     - Category: {insight.category}")
                print(f"     - Headline: {insight.headline}")
                print(f"     - Summary: {insight.summary[:100]}...")
                print(f"     - Evidence: {len(insight.evidence.block_heights)} blocks, "
                      f"{len(insight.evidence.transaction_ids)} transactions")
            else:
                print(f"   ✗ Failed to generate insight")
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    # Step 5: Demonstrate batch processing
    print("\n5. Demonstrating batch processing...")
    
    try:
        insights = await module.generate_insights_batch(signals)
        print(f"   ✓ Generated {len(insights)} insights from {len(signals)} signals")
        
        for insight in insights:
            print(f"     - {insight.category}: {insight.headline[:50]}...")
            
    except Exception as e:
        print(f"   ✗ Batch processing error: {e}")
    
    # Step 6: Show insight dictionary format (for BigQuery)
    print("\n6. Insight dictionary format (for BigQuery persistence):")
    
    if insights:
        sample_insight = insights[0]
        insight_dict = sample_insight.to_dict()
        
        print(f"   {{\n"
              f"     'insight_id': '{insight_dict['insight_id']}',\n"
              f"     'signal_id': '{insight_dict['signal_id']}',\n"
              f"     'category': '{insight_dict['category']}',\n"
              f"     'headline': '{insight_dict['headline'][:40]}...',\n"
              f"     'confidence': {insight_dict['confidence']},\n"
              f"     'evidence': {{\n"
              f"       'block_heights': {insight_dict['evidence']['block_heights']},\n"
              f"       'transaction_ids': {len(insight_dict['evidence']['transaction_ids'])} items\n"
              f"     }},\n"
              f"     'chart_url': {insight_dict['chart_url']},\n"
              f"     'created_at': '{insight_dict['created_at']}'\n"
              f"   }}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
