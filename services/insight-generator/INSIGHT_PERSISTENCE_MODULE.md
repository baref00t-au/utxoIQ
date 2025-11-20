# Insight Persistence Module

## Overview

The Insight Persistence Module handles writing AI-generated insights to BigQuery's `intel.insights` table. It provides robust error handling, automatic retry mechanisms, and comprehensive logging for debugging and monitoring.

## Features

- ✅ Write insights to BigQuery with all required fields
- ✅ Set `chart_url` to null initially (populated later by chart-renderer)
- ✅ Return `insight_id` on successful persistence
- ✅ Handle persistence failures with proper error logging
- ✅ Mark signals as unprocessed for retry on failure
- ✅ Batch persistence support for multiple insights
- ✅ Query utilities for verification and debugging

## Requirements Addressed

- **4.1**: Write insight records to intel.insights BigQuery table
- **4.3**: Return insight_id on successful persistence
- **4.4**: Log errors with signal_id context and mark signal as unprocessed for retry
- **4.5**: Set chart_url field to null for later population

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ InsightPersistenceModule                                    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ persist_insight(insight, correlation_id)             │  │
│  │  - Converts insight to BigQuery format              │  │
│  │  - Sets chart_url to null                           │  │
│  │  - Inserts row into intel.insights table            │  │
│  │  - Returns PersistenceResult with insight_id        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ _mark_signal_unprocessed(signal_id)                 │  │
│  │  - Called on persistence failure                    │  │
│  │  - Updates signal: processed=false, processed_at=NULL│ │
│  │  - Enables retry in next polling cycle              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ persist_insights_batch(insights)                    │  │
│  │  - Batch processing for multiple insights           │  │
│  │  - Returns summary of successes and failures        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Basic Usage

```python
from google.cloud import bigquery
from insight_persistence import InsightPersistenceModule
from insight_generation import Insight, Evidence

# Initialize BigQuery client
bq_client = bigquery.Client(project="utxoiq-dev")

# Initialize persistence module
persistence = InsightPersistenceModule(
    bigquery_client=bq_client,
    project_id="utxoiq-dev",
    dataset_id="intel"
)

# Create an insight (typically from InsightGenerationModule)
insight = Insight(
    insight_id="550e8400-e29b-41d4-a716-446655440000",
    signal_id="123e4567-e89b-12d3-a456-426614174000",
    category="mempool",
    headline="Bitcoin Fees Spike 25% as Mempool Congestion Increases",
    summary="Transaction fees have surged to 50.5 sat/vB, marking a 25% increase...",
    confidence=0.85,
    evidence=Evidence(
        block_heights=[820000],
        transaction_ids=["abc123...", "def456..."]
    ),
    chart_url=None,  # Will be populated later by chart-renderer
    created_at=datetime.utcnow()
)

# Persist the insight
result = await persistence.persist_insight(
    insight=insight,
    correlation_id="req-12345"
)

if result.success:
    print(f"✅ Insight persisted: {result.insight_id}")
else:
    print(f"❌ Persistence failed: {result.error}")
```

### Batch Persistence

```python
# Persist multiple insights at once
insights = [insight1, insight2, insight3]

results = await persistence.persist_insights_batch(
    insights=insights,
    correlation_id="req-12345"
)

print(f"✅ Succeeded: {results['success_count']}")
print(f"❌ Failed: {results['failure_count']}")
print(f"Insight IDs: {results['insight_ids']}")
```

### Query Utilities

```python
# Retrieve an insight by ID
insight_data = await persistence.get_insight_by_id(
    insight_id="550e8400-e29b-41d4-a716-446655440000"
)

# Get all insights for a signal
insights = await persistence.get_insights_by_signal_id(
    signal_id="123e4567-e89b-12d3-a456-426614174000"
)
```

## BigQuery Schema

The module writes to the `intel.insights` table with the following schema:

```sql
CREATE TABLE `utxoiq-dev.intel.insights` (
    insight_id STRING NOT NULL,           -- UUID
    signal_id STRING NOT NULL,            -- Reference to intel.signals
    category STRING NOT NULL,             -- mempool|exchange|miner|whale|treasury|predictive
    headline STRING NOT NULL,             -- Max 80 chars
    summary STRING NOT NULL,              -- 2-3 sentences
    confidence FLOAT64 NOT NULL,          -- 0.0 to 1.0 (inherited from signal)
    evidence STRUCT<
        block_heights ARRAY<INT64>,       -- Block heights referenced
        transaction_ids ARRAY<STRING>     -- Transaction IDs referenced
    >,
    chart_url STRING,                     -- NULL initially, populated by chart-renderer
    created_at TIMESTAMP NOT NULL         -- When insight was created
)
PARTITION BY DATE(created_at)
CLUSTER BY category, confidence;
```

## Error Handling

### Persistence Failures

When insight persistence fails, the module:

1. **Logs the error** with full context:
   - Signal ID
   - Insight ID
   - Error message
   - Correlation ID (if provided)

2. **Marks signal as unprocessed**:
   - Updates `intel.signals` table
   - Sets `processed = false`
   - Sets `processed_at = NULL`
   - Enables retry in next polling cycle

3. **Returns error details**:
   - `PersistenceResult` with `success=False`
   - Error message for debugging

### Example Error Scenarios

**Table Not Found:**
```python
# If intel.insights table doesn't exist
result = await persistence.persist_insight(insight)
# Returns: PersistenceResult(success=False, error="Table utxoiq-dev.intel.insights not found")
# Signal marked as unprocessed for retry
```

**BigQuery Insert Error:**
```python
# If BigQuery insert fails (schema mismatch, quota exceeded, etc.)
result = await persistence.persist_insight(insight)
# Returns: PersistenceResult(success=False, error="BigQuery insert errors: [...]")
# Signal marked as unprocessed for retry
```

**Unexpected Exception:**
```python
# If any unexpected error occurs
result = await persistence.persist_insight(insight)
# Returns: PersistenceResult(success=False, error="Unexpected error: ...")
# Signal marked as unprocessed for retry
```

## Logging

The module uses structured logging with the following levels:

### INFO Level
- Module initialization
- Successful persistence operations
- Batch operation summaries

### WARNING Level
- Signal marked as unprocessed for retry
- Signal not found when marking unprocessed

### ERROR Level
- Persistence failures with full context
- BigQuery errors
- Query failures

### DEBUG Level
- Query results
- Insight retrieval operations

### Example Log Output

```json
{
  "level": "INFO",
  "message": "Persisting insight 550e8400-e29b-41d4-a716-446655440000 for signal 123e4567-e89b-12d3-a456-426614174000",
  "insight_id": "550e8400-e29b-41d4-a716-446655440000",
  "signal_id": "123e4567-e89b-12d3-a456-426614174000",
  "category": "mempool",
  "correlation_id": "req-12345"
}

{
  "level": "INFO",
  "message": "Successfully persisted insight 550e8400-e29b-41d4-a716-446655440000",
  "insight_id": "550e8400-e29b-41d4-a716-446655440000",
  "signal_id": "123e4567-e89b-12d3-a456-426614174000",
  "category": "mempool",
  "correlation_id": "req-12345"
}
```

## Integration with Pipeline

The Insight Persistence Module integrates with the complete pipeline:

```
┌─────────────────┐
│ Signal Polling  │
│ Module          │
└────────┬────────┘
         │ Unprocessed signals
         ▼
┌─────────────────┐
│ Insight         │
│ Generation      │
│ Module          │
└────────┬────────┘
         │ Generated insights
         ▼
┌─────────────────┐
│ Insight         │◄─── YOU ARE HERE
│ Persistence     │
│ Module          │
└────────┬────────┘
         │
         ├─ Success ──► Mark signal as processed
         │
         └─ Failure ──► Mark signal as unprocessed (retry)
```

## Configuration

The module accepts the following configuration parameters:

```python
InsightPersistenceModule(
    bigquery_client: bigquery.Client,  # Required: BigQuery client instance
    project_id: str = "utxoiq-dev",    # GCP project ID
    dataset_id: str = "intel"          # BigQuery dataset ID
)
```

### Environment Variables

No environment variables are required. Configuration is passed via constructor.

## Testing

### Unit Tests

```python
# Test successful persistence
async def test_persist_insight_success():
    mock_client = Mock()
    mock_client.insert_rows_json.return_value = []  # No errors
    
    persistence = InsightPersistenceModule(mock_client)
    result = await persistence.persist_insight(insight)
    
    assert result.success is True
    assert result.insight_id == insight.insight_id

# Test persistence failure
async def test_persist_insight_failure():
    mock_client = Mock()
    mock_client.insert_rows_json.return_value = [{"error": "Schema mismatch"}]
    
    persistence = InsightPersistenceModule(mock_client)
    result = await persistence.persist_insight(insight)
    
    assert result.success is False
    assert result.error is not None
```

### Integration Tests

```python
# Test with real BigQuery (dev environment)
async def test_persist_insight_integration():
    bq_client = bigquery.Client(project="utxoiq-dev")
    persistence = InsightPersistenceModule(bq_client)
    
    result = await persistence.persist_insight(test_insight)
    
    assert result.success is True
    
    # Verify insight was written
    retrieved = await persistence.get_insight_by_id(result.insight_id)
    assert retrieved is not None
    assert retrieved["headline"] == test_insight.headline
```

## Performance Considerations

### Single Insight Persistence
- **Latency**: ~100-500ms per insight
- **Throughput**: ~2-10 insights per second

### Batch Persistence
- **Latency**: ~500ms-2s for 10 insights
- **Throughput**: ~5-20 insights per second
- **Recommendation**: Use batch for >3 insights

### Optimization Tips

1. **Use batch operations** when processing multiple insights
2. **Reuse BigQuery client** across operations
3. **Enable connection pooling** in BigQuery client
4. **Monitor BigQuery quotas** to avoid rate limiting

## Troubleshooting

### Issue: "Table not found"
**Solution**: Ensure `intel.insights` table exists in BigQuery
```bash
bq mk --table utxoiq-dev:intel.insights schema.json
```

### Issue: "Schema mismatch"
**Solution**: Verify insight data matches BigQuery schema
```python
# Check insight structure
print(insight.to_dict())
```

### Issue: "Quota exceeded"
**Solution**: Implement rate limiting or increase BigQuery quota
```python
# Add delay between operations
await asyncio.sleep(0.1)
```

### Issue: "Signal not marked as unprocessed"
**Solution**: Check signal exists in intel.signals table
```sql
SELECT * FROM `utxoiq-dev.intel.signals` WHERE signal_id = 'xxx';
```

## Future Enhancements

1. **Retry with exponential backoff** for transient failures
2. **Bulk insert optimization** using BigQuery streaming API
3. **Automatic schema validation** before insert
4. **Metrics emission** to Cloud Monitoring
5. **Dead letter queue** for permanently failed insights

## Related Modules

- **InsightGenerationModule**: Generates insights from signals
- **SignalPollingModule**: Polls for unprocessed signals
- **AIProvider**: Provides AI-generated content
- **Chart Renderer**: Populates chart_url field (future)

## Support

For issues or questions:
1. Check logs for error details
2. Verify BigQuery table schema
3. Test with example usage script
4. Review requirements documentation
