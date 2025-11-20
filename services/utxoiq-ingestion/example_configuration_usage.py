"""
Example: Using ConfigurationModule with Signal Processors

This example demonstrates how to use the ConfigurationModule to:
1. Load processor configurations from environment variables
2. Initialize processors with their configurations
3. Check for configuration updates and hot-reload
4. Use the configuration with the Pipeline Orchestrator
"""

import asyncio
import os
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import ConfigurationModule, ProcessorConfig


def example_basic_usage():
    """Example 1: Basic configuration loading"""
    print("=" * 60)
    print("Example 1: Basic Configuration Loading")
    print("=" * 60)
    
    # Initialize configuration module
    config_module = ConfigurationModule()
    
    # Get all processor configurations
    all_configs = config_module.get_all_configs()
    print(f"\nTotal processors configured: {len(all_configs)}")
    
    # Display each processor's configuration
    for processor_type, config in all_configs.items():
        print(f"\n{processor_type.upper()} Processor:")
        print(f"  Enabled: {config.enabled}")
        print(f"  Confidence Threshold: {config.confidence_threshold}")
        print(f"  Time Window: {config.time_window}")
        
        # Show processor-specific settings
        if processor_type == "whale" and hasattr(config, 'threshold_btc'):
            print(f"  Whale Threshold: {config.threshold_btc} BTC")
        elif processor_type == "mempool" and hasattr(config, 'spike_threshold'):
            print(f"  Spike Threshold: {config.spike_threshold}x")


def example_enabled_processors():
    """Example 2: Getting only enabled processors"""
    print("\n" + "=" * 60)
    print("Example 2: Getting Enabled Processors")
    print("=" * 60)
    
    config_module = ConfigurationModule()
    
    # Get only enabled processors
    enabled = config_module.get_enabled_processors()
    
    print(f"\nEnabled processors: {len(enabled)}")
    for processor_type in enabled.keys():
        print(f"  ✓ {processor_type}")
    
    # Check specific processor
    if config_module.is_processor_enabled("mempool"):
        print("\n✓ Mempool processor is enabled")
    else:
        print("\n✗ Mempool processor is disabled")


def example_hot_reload():
    """Example 3: Configuration hot-reload"""
    print("\n" + "=" * 60)
    print("Example 3: Configuration Hot-Reload")
    print("=" * 60)
    
    config_module = ConfigurationModule()
    
    print(f"\nInitial state:")
    print(f"  Mempool enabled: {config_module.config['mempool'].enabled}")
    print(f"  Last reload: {config_module.last_reload.strftime('%H:%M:%S')}")
    
    # Check if reload is needed
    if config_module.should_reload():
        print("\n⚠ Configuration reload needed (5 minutes elapsed)")
        config_module.reload_config()
        print("✓ Configuration reloaded")
    else:
        print("\n✓ Configuration is up to date (no reload needed)")
    
    print(f"\nAfter reload check:")
    print(f"  Mempool enabled: {config_module.config['mempool'].enabled}")
    print(f"  Last reload: {config_module.last_reload.strftime('%H:%M:%S')}")


def example_with_processors():
    """Example 4: Using configuration with signal processors"""
    print("\n" + "=" * 60)
    print("Example 4: Using Configuration with Processors")
    print("=" * 60)
    
    config_module = ConfigurationModule()
    
    # Simulate creating processors with configuration
    print("\nInitializing processors with configuration:")
    
    for processor_type in ["mempool", "exchange", "miner", "whale"]:
        config = config_module.get_processor_config(processor_type)
        
        if config and config.enabled:
            print(f"\n✓ {processor_type.upper()} Processor")
            print(f"  Status: Enabled")
            print(f"  Confidence Threshold: {config.confidence_threshold}")
            print(f"  Time Window: {config.time_window}")
            
            # In real usage, you would pass this config to the processor:
            # processor = MempoolProcessor(config)
        else:
            print(f"\n✗ {processor_type.upper()} Processor")
            print(f"  Status: Disabled (skipped)")


def example_environment_override():
    """Example 5: Environment variable override"""
    print("\n" + "=" * 60)
    print("Example 5: Environment Variable Override")
    print("=" * 60)
    
    # Set custom environment variables
    print("\nSetting custom environment variables:")
    print("  WHALE_PROCESSOR_ENABLED=false")
    print("  CONFIDENCE_THRESHOLD=0.85")
    print("  WHALE_THRESHOLD_BTC=2000")
    
    os.environ["WHALE_PROCESSOR_ENABLED"] = "false"
    os.environ["CONFIDENCE_THRESHOLD"] = "0.85"
    os.environ["WHALE_THRESHOLD_BTC"] = "2000"
    
    # Create new configuration module (reads env vars)
    config_module = ConfigurationModule()
    
    print("\nConfiguration after override:")
    print(f"  Whale enabled: {config_module.config['whale'].enabled}")
    print(f"  Exchange threshold: {config_module.config['exchange'].confidence_threshold}")
    print(f"  Whale BTC threshold: {config_module.config['whale'].threshold_btc}")
    
    # Clean up
    del os.environ["WHALE_PROCESSOR_ENABLED"]
    del os.environ["CONFIDENCE_THRESHOLD"]
    del os.environ["WHALE_THRESHOLD_BTC"]


async def example_periodic_reload():
    """Example 6: Periodic configuration reload in background"""
    print("\n" + "=" * 60)
    print("Example 6: Periodic Configuration Reload")
    print("=" * 60)
    
    config_module = ConfigurationModule()
    
    print("\nSimulating periodic reload check (every 5 minutes):")
    print("In production, this would run as a background task\n")
    
    # Simulate checking for reload
    for i in range(3):
        print(f"Check {i+1}:")
        
        if config_module.should_reload():
            print("  ⚠ Reload needed - reloading configuration...")
            config_module.reload_config()
            print("  ✓ Configuration reloaded")
        else:
            elapsed = (datetime.utcnow() - config_module.last_reload).total_seconds() / 60
            print(f"  ✓ No reload needed ({elapsed:.1f} minutes since last reload)")
        
        # In production, this would be:
        # await asyncio.sleep(300)  # 5 minutes
        await asyncio.sleep(0.1)  # Short delay for demo


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("ConfigurationModule Usage Examples")
    print("=" * 60)
    
    # Run synchronous examples
    example_basic_usage()
    example_enabled_processors()
    example_hot_reload()
    example_with_processors()
    example_environment_override()
    
    # Run async example
    asyncio.run(example_periodic_reload())
    
    print("\n" + "=" * 60)
    print("Examples Complete")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. ConfigurationModule loads settings from environment variables")
    print("2. Supports hot-reload every 5 minutes without restart")
    print("3. Each processor can have custom thresholds and settings")
    print("4. Easy to check which processors are enabled")
    print("5. Configuration can be overridden via environment variables")
    print("\nFor production use:")
    print("- Set environment variables in .env file or Cloud Run config")
    print("- Use config_module.should_reload() in background task")
    print("- Pass processor configs to processor constructors")
    print("=" * 60)


if __name__ == "__main__":
    main()
