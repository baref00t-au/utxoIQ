# Configuration Module Guide

## Overview

The `ConfigurationModule` provides centralized configuration management for all signal processors in the utxoiq-ingestion service. It supports:

- Loading processor settings from environment variables
- Hot-reload without service restart (every 5 minutes)
- Per-processor configuration (enabled flags, thresholds, time windows)
- Easy integration with the Pipeline Orchestrator

## Quick Start

### 1. Basic Usage

```python
from src.config import ConfigurationModule

# Initialize configuration module
config_module = ConfigurationModule()

# Get configuration for a specific processor
mempool_config = config_module.get_processor_config("mempool")

# Check if processor is enabled
if config_module.is_processor_enabled("mempool"):
    print("Mempool processor is enabled")

# Get all enabled processors
enabled_processors = config_module.get_enabled_processors()
```

### 2. Integration with Signal Processors

```python
from src.config import ConfigurationModule
from src.processors.mempool_processor import MempoolProcessor
from src.processors.exchange_processor import ExchangeProcessor

# Initialize configuration
config_module = ConfigurationModule()

# Create processors with their configurations
processors = []

if config_module.is_processor_enabled("mempool"):
    mempool_config = config_module.get_processor_config("mempool")
    processors.append(MempoolProcessor(mempool_config))

if config_module.is_processor_enabled("exchange"):
    exchange_config = config_module.get_processor_config("exchange")
    processors.append(ExchangeProcessor(exchange_config))

# Pass processors to Pipeline Orchestrator
orchestrator = PipelineOrchestrator(
    signal_processors=processors,
    signal_persistence=persistence_module
)
```

### 3. Hot-Reload in Background Task

```python
import asyncio
from src.config import ConfigurationModule

async def config_reload_task(config_module: ConfigurationModule):
    """Background task to check for configuration updates"""
    while True:
        # Wait 5 minutes
        await asyncio.sleep(300)
        
        # Check if reload is needed
        if config_module.should_reload():
            config_module.reload_config()
            logger.info("Configuration reloaded")
            
            # Optionally: Recreate processors with new config
            # update_processors(config_module)

# Start background task
config_module = ConfigurationModule()
asyncio.create_task(config_reload_task(config_module))
```

## Environment Variables

### Global Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIDENCE_THRESHOLD` | `0.7` | Global confidence threshold for all processors |

### Processor Toggles

Enable or disable individual processors:

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMPOOL_PROCESSOR_ENABLED` | `true` | Enable mempool fee analysis |
| `EXCHANGE_PROCESSOR_ENABLED` | `true` | Enable exchange flow tracking |
| `MINER_PROCESSOR_ENABLED` | `true` | Enable mining pool activity |
| `WHALE_PROCESSOR_ENABLED` | `true` | Enable whale movement detection |
| `TREASURY_PROCESSOR_ENABLED` | `true` | Enable corporate treasury tracking |
| `PREDICTIVE_PROCESSOR_ENABLED` | `true` | Enable predictive analytics |

### Per-Processor Confidence Thresholds

Override the global confidence threshold for specific processors:

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMPOOL_CONFIDENCE_THRESHOLD` | `0.7` | Mempool signal confidence threshold |
| `EXCHANGE_CONFIDENCE_THRESHOLD` | `0.7` | Exchange signal confidence threshold |
| `MINER_CONFIDENCE_THRESHOLD` | `0.7` | Miner signal confidence threshold |
| `WHALE_CONFIDENCE_THRESHOLD` | `0.7` | Whale signal confidence threshold |
| `TREASURY_CONFIDENCE_THRESHOLD` | `0.7` | Treasury signal confidence threshold |
| `PREDICTIVE_CONFIDENCE_THRESHOLD` | `0.5` | Predictive signal confidence threshold |

### Time Windows

Configure historical comparison time windows:

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMPOOL_TIME_WINDOW` | `1h` | Mempool comparison window |
| `EXCHANGE_TIME_WINDOW` | `24h` | Exchange flow comparison window |
| `MINER_TIME_WINDOW` | `7d` | Miner activity comparison window |
| `WHALE_TIME_WINDOW` | `24h` | Whale movement comparison window |
| `TREASURY_TIME_WINDOW` | `24h` | Treasury activity comparison window |
| `PREDICTIVE_TIME_WINDOW` | `24h` | Predictive model training window |

### Processor-Specific Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMPOOL_SPIKE_THRESHOLD` | `1.2` | Fee spike multiplier (1.2 = 20% increase) |
| `WHALE_THRESHOLD_BTC` | `1000` | Minimum BTC for whale classification |
| `PREDICTIVE_MIN_CONFIDENCE` | `0.5` | Minimum confidence for predictive signals |

## Configuration Examples

### Example 1: Disable Predictive Processor

```bash
# .env file
PREDICTIVE_PROCESSOR_ENABLED=false
```

### Example 2: High Confidence Mode

```bash
# .env file
CONFIDENCE_THRESHOLD=0.85
WHALE_CONFIDENCE_THRESHOLD=0.9
```

### Example 3: Aggressive Whale Detection

```bash
# .env file
WHALE_THRESHOLD_BTC=500
WHALE_CONFIDENCE_THRESHOLD=0.75
```

### Example 4: Custom Time Windows

```bash
# .env file
MEMPOOL_TIME_WINDOW=30m
EXCHANGE_TIME_WINDOW=12h
MINER_TIME_WINDOW=14d
```

## API Reference

### ConfigurationModule

#### `__init__()`

Initialize the configuration module and load settings from environment variables.

```python
config_module = ConfigurationModule()
```

#### `get_processor_config(processor_type: str) -> Optional[ProcessorConfig]`

Get configuration for a specific processor type.

**Parameters:**
- `processor_type`: One of "mempool", "exchange", "miner", "whale", "treasury", "predictive"

**Returns:**
- `ProcessorConfig` object or `None` if not found

```python
config = config_module.get_processor_config("mempool")
```

#### `get_all_configs() -> Dict[str, ProcessorConfig]`

Get all processor configurations.

**Returns:**
- Dictionary mapping processor type to `ProcessorConfig`

```python
all_configs = config_module.get_all_configs()
```

#### `get_enabled_processors() -> Dict[str, ProcessorConfig]`

Get only enabled processor configurations.

**Returns:**
- Dictionary mapping processor type to `ProcessorConfig` for enabled processors only

```python
enabled = config_module.get_enabled_processors()
```

#### `is_processor_enabled(processor_type: str) -> bool`

Check if a specific processor is enabled.

**Parameters:**
- `processor_type`: Processor type to check

**Returns:**
- `True` if enabled, `False` otherwise

```python
if config_module.is_processor_enabled("mempool"):
    # Process mempool signals
```

#### `get_confidence_threshold(processor_type: str) -> float`

Get confidence threshold for a specific processor.

**Parameters:**
- `processor_type`: Processor type

**Returns:**
- Confidence threshold (0.0 to 1.0), or 0.7 as default

```python
threshold = config_module.get_confidence_threshold("whale")
```

#### `should_reload() -> bool`

Check if configuration should be reloaded (5-minute interval elapsed).

**Returns:**
- `True` if reload needed, `False` otherwise

```python
if config_module.should_reload():
    config_module.reload_config()
```

#### `reload_config() -> None`

Hot-reload configuration from environment variables without service restart.

```python
config_module.reload_config()
```

### ProcessorConfig

#### Attributes

- `enabled: bool` - Whether processor is enabled
- `confidence_threshold: float` - Minimum confidence score
- `time_window: str` - Time window for historical comparisons
- Additional processor-specific attributes (e.g., `threshold_btc` for whale processor)

## Integration with Pipeline Orchestrator

The `ConfigurationModule` is designed to work seamlessly with the `PipelineOrchestrator`:

```python
from src.config import ConfigurationModule
from src.pipeline_orchestrator import PipelineOrchestrator
from src.signal_persistence import SignalPersistenceModule
from src.processors.mempool_processor import MempoolProcessor
from src.processors.exchange_processor import ExchangeProcessor
from src.processors.miner_processor import MinerProcessor
from src.processors.whale_processor import WhaleProcessor
from src.processors.treasury_processor import TreasuryProcessor
from src.processors.predictive_analytics import PredictiveAnalyticsModule

# Initialize configuration
config_module = ConfigurationModule()

# Create processors based on configuration
processors = []

processor_classes = {
    "mempool": MempoolProcessor,
    "exchange": ExchangeProcessor,
    "miner": MinerProcessor,
    "whale": WhaleProcessor,
    "treasury": TreasuryProcessor,
    "predictive": PredictiveAnalyticsModule
}

for processor_type, processor_class in processor_classes.items():
    if config_module.is_processor_enabled(processor_type):
        config = config_module.get_processor_config(processor_type)
        processor = processor_class(config)
        processors.append(processor)
        logger.info(f"Initialized {processor_type} processor")

# Initialize pipeline orchestrator
orchestrator = PipelineOrchestrator(
    signal_processors=processors,
    signal_persistence=persistence_module,
    monitoring_module=monitoring_module
)

# Process blocks
result = await orchestrator.process_new_block(block_data)
```

## Best Practices

### 1. Use Environment Variables for Configuration

Always configure processors via environment variables rather than hardcoding values:

```python
# ✓ Good
config_module = ConfigurationModule()

# ✗ Bad
processor = MempoolProcessor(
    ProcessorConfig(enabled=True, confidence_threshold=0.7)
)
```

### 2. Check Enabled Status Before Processing

Always check if a processor is enabled before using it:

```python
# ✓ Good
if config_module.is_processor_enabled("mempool"):
    processor = MempoolProcessor(config_module.get_processor_config("mempool"))

# ✗ Bad
processor = MempoolProcessor(config_module.get_processor_config("mempool"))
```

### 3. Implement Hot-Reload in Production

Use a background task to check for configuration updates:

```python
async def config_reload_task():
    while True:
        await asyncio.sleep(300)  # 5 minutes
        if config_module.should_reload():
            config_module.reload_config()
```

### 4. Log Configuration Changes

Always log when configuration is reloaded:

```python
if config_module.should_reload():
    logger.info("Reloading configuration")
    config_module.reload_config()
    logger.info("Configuration reloaded successfully")
```

### 5. Validate Configuration on Startup

Verify configuration is correct when service starts:

```python
config_module = ConfigurationModule()
enabled_count = len(config_module.get_enabled_processors())
logger.info(f"Configuration loaded: {enabled_count} processors enabled")
```

## Troubleshooting

### Configuration Not Loading

**Problem:** Environment variables not being read

**Solution:** Ensure `.env` file exists and is in the correct location:

```bash
# Check .env file location
ls services/utxoiq-ingestion/.env

# Verify environment variables are set
echo $MEMPOOL_PROCESSOR_ENABLED
```

### Hot-Reload Not Working

**Problem:** Configuration changes not taking effect

**Solution:** Verify reload interval has elapsed:

```python
# Check last reload time
print(f"Last reload: {config_module.last_reload}")
print(f"Should reload: {config_module.should_reload()}")
```

### Processor Not Running

**Problem:** Processor is configured but not generating signals

**Solution:** Check if processor is enabled:

```python
# Verify processor is enabled
print(f"Mempool enabled: {config_module.is_processor_enabled('mempool')}")

# Check configuration
config = config_module.get_processor_config("mempool")
print(f"Config: {config}")
```

## Requirements Satisfied

This implementation satisfies the following requirements from the design document:

- **Requirement 7.1**: Load processor settings from environment variables
- **Requirement 7.2**: Only invoke processors where enabled=true
- **Requirement 7.3**: Apply configured confidence threshold
- **Requirement 7.4**: Allow hot-reload without service restart (5-minute polling)
- **Requirement 7.5**: Log configuration changes for audit purposes

## See Also

- [Pipeline Orchestrator Documentation](./docs/pipeline-orchestrator.md)
- [Signal Processor Guide](./docs/signal-processors.md)
- [Environment Variables Reference](./.env.example)
