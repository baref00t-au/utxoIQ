"""
Example usage of AI Provider Module

This script demonstrates how to use the AI provider module
to generate insights from signals.

Requirements: 8.1, 8.6
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_provider import (
    get_configured_provider,
    AIProviderFactory,
    AIProviderError,
    Signal
)


# Sample prompt template
MEMPOOL_TEMPLATE = """
You are a Bitcoin blockchain analyst. Generate a concise insight about this mempool signal.

Signal Data:
- Fee Rate: {fee_rate_median} sat/vB
- Change: {fee_rate_change_pct}% vs {comparison_window}
- Mempool Size: {mempool_size_mb} MB
- Transaction Count: {tx_count}

Provide:
1. Headline (max 80 chars)
2. Summary (2-3 sentences explaining why this matters)
3. Confidence Explanation (why this signal is reliable)

Format as JSON:
{{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}}
"""


async def example_basic_usage():
    """Example 1: Basic usage with environment configuration"""
    print("\n=== Example 1: Basic Usage ===\n")
    
    try:
        # Get provider from environment
        provider = get_configured_provider()
        print(f"✓ Loaded provider: {provider.provider_name}")
        
        # Create sample signal
        signal = Signal(
            signal_id="example-signal-001",
            signal_type="mempool",
            block_height=800000,
            confidence=0.85,
            metadata={
                "fee_rate_median": 50.5,
                "fee_rate_change_pct": 25.3,
                "tx_count": 15000,
                "mempool_size_mb": 120.5,
                "comparison_window": "1h"
            }
        )
        print(f"✓ Created signal: {signal.signal_id}")
        
        # Generate insight
        print("\nGenerating insight...")
        insight_content = await provider.generate_insight(signal, MEMPOOL_TEMPLATE)
        
        print("\n--- Generated Insight ---")
        print(f"Headline: {insight_content.headline}")
        print(f"\nSummary: {insight_content.summary}")
        print(f"\nConfidence: {insight_content.confidence_explanation}")
        
    except AIProviderError as e:
        print(f"✗ AI Provider Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")


async def example_specific_provider():
    """Example 2: Using a specific provider with custom config"""
    print("\n=== Example 2: Specific Provider ===\n")
    
    # Check if OpenAI is configured
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠ Skipping: OPENAI_API_KEY not set")
        return
    
    try:
        # Create OpenAI provider with custom config
        config = {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-4-turbo"
        }
        
        provider = AIProviderFactory.create_provider("openai", config)
        print(f"✓ Created OpenAI provider with model: {provider.model}")
        
        # Create signal
        signal = Signal(
            signal_id="example-signal-002",
            signal_type="exchange",
            block_height=800001,
            confidence=0.92,
            metadata={
                "entity_name": "Coinbase",
                "flow_type": "outflow",
                "amount_btc": 1250.5,
                "tx_count": 45,
                "block_height": 800001
            }
        )
        
        # Exchange prompt template
        exchange_template = """
You are a Bitcoin blockchain analyst. Generate a concise insight about this exchange flow signal.

Signal Data:
- Exchange: {entity_name}
- Flow Type: {flow_type}
- Amount: {amount_btc} BTC
- Transaction Count: {tx_count}
- Block Height: {block_height}

Provide:
1. Headline (max 80 chars, mention exchange name)
2. Summary (2-3 sentences explaining market implications)
3. Confidence Explanation (why this signal is reliable)

Format as JSON:
{{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}}
"""
        
        print("\nGenerating insight with OpenAI...")
        insight_content = await provider.generate_insight(signal, exchange_template)
        
        print("\n--- Generated Insight ---")
        print(f"Headline: {insight_content.headline}")
        print(f"\nSummary: {insight_content.summary}")
        
    except AIProviderError as e:
        print(f"✗ AI Provider Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")


async def example_error_handling():
    """Example 3: Error handling"""
    print("\n=== Example 3: Error Handling ===\n")
    
    try:
        # Try to create provider with invalid type
        print("Attempting to create invalid provider...")
        provider = AIProviderFactory.create_provider("invalid_provider", {})
        
    except AIProviderError as e:
        print(f"✓ Caught expected error: {e}")
    
    try:
        # Try to create provider with missing config
        print("\nAttempting to create OpenAI provider without API key...")
        provider = AIProviderFactory.create_provider("openai", {})
        
    except AIProviderError as e:
        print(f"✓ Caught expected error: {e}")


async def example_multiple_signals():
    """Example 4: Processing multiple signals"""
    print("\n=== Example 4: Multiple Signals ===\n")
    
    try:
        provider = get_configured_provider()
        print(f"✓ Loaded provider: {provider.provider_name}")
        
        # Create multiple signals
        signals = [
            Signal(
                signal_id=f"signal-{i}",
                signal_type="mempool",
                block_height=800000 + i,
                confidence=0.8 + (i * 0.05),
                metadata={
                    "fee_rate_median": 50.0 + i,
                    "fee_rate_change_pct": 20.0 + i,
                    "tx_count": 15000,
                    "mempool_size_mb": 120.0,
                    "comparison_window": "1h"
                }
            )
            for i in range(3)
        ]
        
        print(f"✓ Created {len(signals)} signals")
        
        # Process signals
        print("\nProcessing signals...")
        for signal in signals:
            try:
                insight = await provider.generate_insight(signal, MEMPOOL_TEMPLATE)
                print(f"✓ {signal.signal_id}: {insight.headline[:50]}...")
            except AIProviderError as e:
                print(f"✗ {signal.signal_id}: Failed - {e}")
        
    except Exception as e:
        print(f"✗ Error: {e}")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("AI Provider Module - Usage Examples")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check configuration
    ai_provider = os.getenv("AI_PROVIDER")
    if not ai_provider:
        print("\n⚠ Warning: AI_PROVIDER environment variable not set")
        print("Please set AI_PROVIDER to one of: vertex_ai, openai, anthropic, grok")
        print("\nExample:")
        print("  export AI_PROVIDER=vertex_ai")
        print("  export VERTEX_AI_PROJECT=your-project-id")
        return
    
    print(f"\nConfigured Provider: {ai_provider}")
    
    # Run examples
    await example_basic_usage()
    await example_specific_provider()
    await example_error_handling()
    await example_multiple_signals()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
