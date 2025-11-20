# Signal Polling Module

The Signal Polling Module is responsible for querying BigQuery for unprocessed signals and managing their processing state in the insight-generator service.

## Overview

The module polls the `intel.signals` BigQuery table for signals that:
- Have `processed = false`
- Have `confidence >= 0.7` (configurable threshold)
- Are of supported types: mempool, exchange, miner, whale, treasury, predictive

Signals are grouped by `signal_type` and `block_height` for efficient batch processing.

## Key Components

### SignalPollingModule

Main class that handles signal polling and state management.

**Initialization:**
```python
from google.cloud import bigquery
from src.signal_polling import SignalPollingModule

bq_client = bigquery.Client(project="utxoiq-dev")

polling_module = SignalPollingModule(
    bigquery_client=bq_client,
    project_id="utxoiq-dev",
    dataset_id="intel",
    confidence_threshold=0.7
)
```

**Key Methods:**

#### `poll_unprocessed_signals(limit=100)`
Queries BigQuery for unprocessed signals and groups them.

```python
signal_groups = await polling_module.poll_unprocessed_signals(limit=50)

for group in signal_groups:
    print(f"Type: {group.signal_type}, Block: {group.block_height}")
    print(f"Signals: {len(group.signals)}")
```

Returns: `List[SignalGroup]`

#### `mark_signal_processed(signal_id, processed_at=None)`
Marks a single signal as processed.

```python
success = await polling_module.mark_signal_processed('signal-123')
```

Returns: `bool` (True if successful)

#### `mark_signals_processed_batch(signal_ids, processed_at=None)`
Marks multiple signals as processed in a single query (more efficient).

```python
signal_ids = ['signal-1', 'signal-2', 'signal-3']
count = await polling_module.mark_signals_processed_batch(signal_ids)
print(f"Marked {count} signals as processed")
```

Returns: `int` (number of signals marked)

#### `get_unprocessed_signal_count()`
Gets the count of unprocessed signals (useful for monitoring).

```python
count = await polling_module.get_unprocessed_signal_count()
print(f"Unprocessed signals: {count}")
```

Returns: `int`

#### `get_stale_signals(max_age_hours=1)`
Gets signals that have been unprocessed for too long (for alerting).

```python
stale_signals = await polling_module.get_stale_signals(max_age_hours=1)
if stale_signals:
    print(f"Warning: {len(stale_signals)} stale signals found!")
```

Returns: `List[Dict]`

### SignalGroup

Dataclass representing a group of signals.

```python
@dataclass
class SignalGroup:
    signal_type: str        # mempool, exchange, miner, whale, treasury, predictive
    block_height: int       # Bitcoin block height
    signals: List[Dict]     # List of signal dictionaries
```

## Usage Patterns

### Basic Polling Workflow

```python
import asyncio
from google.cloud import bigquery
from src.signal_polling import SignalPollingModule

async def process_signals():
    # Initialize
    bq_client = bigquery.Client(project="utxoiq-dev")
    polling_module = SignalPollingModule(bq_client)
    
    # Poll for signals
    signal_groups = await polling_module.poll_unprocessed_signals()
    
    for group in signal_groups:
        # Process each signal in the group
        for signal in group.signals:
            # Generate insight from signal
            insight = await generate_insight(signal)
            await persist_insight(insight)
        
        # Mark all signals in group as processed
        signal_ids = [s['signal_id'] for s in group.signals]
        await polling_module.mark_signals_processed_batch(signal_ids)

asyncio.run(process_signals())
```

### Continuous Polling Loop

```python
async def continuous_polling():
    bq_client = bigquery.Client(project="utxoiq-dev")
    polling_module = SignalPollingModule(bq_client)
    
    while True:
        # Poll for signals
        signal_groups = await polling_module.poll_unprocessed_signals()
        
        if signal_groups:
            # Process signals
            for group in signal_groups:
                await process_signal_group(group)
                
                # Mark as processed
                signal_ids = [s['signal_id'] for s in group.signals]
                await polling_module.mark_signals_processed_batch(signal_ids)
        
        # Wait before next poll
        await asyncio.sleep(10)  # 10 seconds
```

### Monitoring and Alerting

```python
async def monitor_signal_queue():
    bq_client = bigquery.Client(project="utxoiq-dev")
    polling_module = SignalPollingModule(bq_client)
    
    # Check queue size
    count = await polling_module.get_unprocessed_signal_count()
    if count > 100:
        print(f"Warning: Large queue size ({count} signals)")
    
    # Check for stale signals
    stale_signals = await polling_module.get_stale_signals(max_age_hours=1)
    if stale_signals:
        print(f"Alert: {len(stale_signals)} signals stuck in queue!")
        for signal in stale_signals[:5]:
            print(f"  - {signal['signal_id']}: {signal['age_hours']} hours old")
```

## Configuration

### Environment Variables

The module uses the following configuration:

- **Project ID**: GCP project ID (default: "utxoiq-dev")
- **Dataset ID**: BigQuery dataset for intel data (default: "intel")
- **Confidence Threshold**: Minimum confidence for processing (default: 0.7)
- **Poll Interval**: Seconds between polls (default: 10)

### Confidence Threshold

Only signals with `confidence >= threshold` are processed. This filters out low-quality signals and reduces AI costs.

Recommended thresholds:
- **Production**: 0.7 (high-quality insights only)
- **Development**: 0.5 (more signals for testing)
- **Backfill**: 0.8 (only highest confidence for historical data)

## Signal Grouping

Signals are grouped by `signal_type` and `block_height` for efficient processing:

**Benefits:**
- Batch processing reduces overhead
- Related signals processed together
- Easier to generate multi-signal insights
- More efficient BigQuery updates

**Example:**
```
Block 800000:
  - mempool: 2 signals
  - exchange: 1 signal

Block 800001:
  - miner: 1 signal
  - whale: 1 signal
```

Results in 4 groups, each processed independently.

## Error Handling

The module handles errors gracefully:

- **BigQuery errors**: Logged and return empty results
- **Table not found**: Logged and return empty results
- **Update failures**: Logged and return False/0

All errors are logged with context for debugging.

## Performance Considerations

### Query Optimization

- Queries are limited to 100 signals by default
- Signals ordered by `created_at` (oldest first)
- Indexes on `processed`, `confidence`, `signal_type` recommended

### Batch Operations

Use `mark_signals_processed_batch()` instead of multiple `mark_signal_processed()` calls:

```python
# ❌ Slow: Multiple queries
for signal_id in signal_ids:
    await polling_module.mark_signal_processed(signal_id)

# ✅ Fast: Single query
await polling_module.mark_signals_processed_batch(signal_ids)
```

### Poll Interval

Default: 10 seconds

Adjust based on:
- Signal generation rate
- AI provider latency
- Cost constraints

## Integration with Insight Generation

The Signal Polling Module is designed to work with the Insight Generation Module:

```python
from src.signal_polling import SignalPollingModule
from src.insight_generation import InsightGenerationModule
from src.insight_persistence import InsightPersistenceModule

async def generate_insights_from_signals():
    # Initialize modules
    polling = SignalPollingModule(bq_client)
    generation = InsightGenerationModule(ai_provider)
    persistence = InsightPersistenceModule(bq_client)
    
    # Poll for signals
    signal_groups = await polling.poll_unprocessed_signals()
    
    for group in signal_groups:
        for signal in group.signals:
            # Generate insight
            insight = await generation.generate_insight(signal)
            
            # Persist insight
            await persistence.persist_insight(insight)
        
        # Mark signals as processed
        signal_ids = [s['signal_id'] for s in group.signals]
        await polling.mark_signals_processed_batch(signal_ids)
```

## Testing

See `tests/signal_polling.unit.test.py` for comprehensive unit tests.

Run tests:
```bash
pytest tests/signal_polling.unit.test.py -v
```

## Example Usage

See `example_signal_polling_usage.py` for complete examples:

```bash
python example_signal_polling_usage.py
```

## Requirements

Defined in requirements 3.1, 3.2, and 3.5 of the signal-insight-pipeline specification:

- **3.1**: Poll intel.signals for processed=false and confidence>=0.7
- **3.2**: Group signals by signal_type and block_height
- **3.5**: Update processed=true and processed_at timestamp

## Related Modules

- **Insight Generation Module**: Generates insights from signals
- **Insight Persistence Module**: Persists insights to BigQuery
- **AI Provider Module**: Provides AI-powered insight generation
- **Signal Persistence Module**: Persists signals from utxoiq-ingestion

## Future Enhancements

- Real-time signal notifications via Pub/Sub
- Priority-based signal processing
- Automatic retry for failed insights
- Signal deduplication
- Multi-signal insight generation
