# Insight Generation Module

## Overview

The `InsightGenerationModule` is the core component responsible for transforming blockchain signals into human-readable insights using AI providers. It orchestrates the complete insight generation process from signal input to structured insight output ready for persistence.

## Architecture

```
Signal (BigQuery) → InsightGenerationModule → Insight (BigQuery)
                           ↓
                    AI Provider (Vertex AI/OpenAI/Anthropic/Grok)
                           ↓
                    Prompt Templates
```

## Key Components

### 1. InsightGenerationModule

Main class that orchestrates insight generation.

**Responsibilities:**
- Select appropriate prompt template based on signal type
- Invoke AI provider with formatted prompt
- Parse and validate AI responses
- Extract blockchain evidence from signal metadata
- Create complete insight records

**Requirements Addressed:**
- 3.3: Generate insights using AI with appropriate prompt templates
- 3.4: Parse AI response and validate JSON structure
- 4.2: Extract blockchain evidence (block heights, transaction IDs)

### 2. Data Models

#### Signal (Input)
```python
{
    "signal_id": str,           # UUID
    "signal_type": str,         # mempool|exchange|miner|whale|treasury|predictive
    "block_height": int,
    "confidence": float,        # 0.0 to 1.0
    "metadata": dict,           # Signal-specific data
    "created_at": datetime
}
```

#### Insight (Output)
```python
{
    "insight_id": str,          # UUID
    "signal_id": str,           # Reference to source signal
    "category": str,            # Same as signal_type
    "headline": str,            # Max 80 chars
    "summary": str,             # 2-3 sentences
    "confidence": float,        # Inherited from signal
    "evidence": {
        "block_heights": [int],
        "transaction_ids": [str]
    },
    "chart_url": str | None,    # Populated later by chart-renderer
    "created_at": datetime
}
```

#### Evidence
```python
{
    "block_heights": [int],     # Always includes signal's block_height
    "transaction_ids": [str]    # Extracted from metadata
}
```

## Prompt Template Selection

The module automatically selects the appropriate prompt template based on signal type:

| Signal Type | Template | Key Metadata Fields |
|------------|----------|---------------------|
| mempool | `MEMPOOL_TEMPLATE` | fee_rate_median, fee_rate_change_pct, mempool_size_mb, tx_count |
| exchange | `EXCHANGE_TEMPLATE` | entity_name, flow_type, amount_btc, tx_count |
| miner | `MINER_TEMPLATE` | pool_name, amount_btc, treasury_balance_change |
| whale | `WHALE_TEMPLATE` | whale_address, amount_btc, balance_btc |
| treasury | `TREASURY_TEMPLATE` | entity_name, company_ticker, flow_type, amount_btc, known_holdings_btc |
| predictive | `PREDICTIVE_TEMPLATE` | prediction_type, predicted_value, confidence_interval, forecast_horizon |

## Usage

### Basic Usage

```python
from src.insight_generation import InsightGenerationModule
from src.ai_provider import get_configured_provider

# Initialize with AI provider
provider = get_configured_provider()  # Loads from AI_PROVIDER env var
module = InsightGenerationModule(provider)

# Generate insight from signal
signal = {
    "signal_id": "abc-123",
    "signal_type": "mempool",
    "block_height": 800000,
    "confidence": 0.85,
    "metadata": {
        "fee_rate_median": 50.5,
        "fee_rate_change_pct": 25.3,
        "mempool_size_mb": 120.5,
        "tx_count": 15000
    }
}

insight = await module.generate_insight(signal)

if insight:
    print(f"Generated: {insight.headline}")
    print(f"Evidence: {len(insight.evidence.transaction_ids)} transactions")
```

### Batch Processing

```python
# Process multiple signals
signals = [signal1, signal2, signal3]
insights = await module.generate_insights_batch(signals)

print(f"Generated {len(insights)} insights from {len(signals)} signals")
```

### Integration with Signal Polling

```python
from src.signal_polling import SignalPollingModule
from src.insight_generation import InsightGenerationModule
from src.ai_provider import get_configured_provider

# Initialize modules
polling_module = SignalPollingModule(bigquery_client)
ai_provider = get_configured_provider()
insight_module = InsightGenerationModule(ai_provider)

# Poll for unprocessed signals
signal_groups = await polling_module.poll_unprocessed_signals()

# Generate insights for each group
for group in signal_groups:
    insights = await insight_module.generate_insights_batch(group.signals)
    
    # Persist insights (see InsightPersistenceModule)
    for insight in insights:
        await persistence_module.persist_insight(insight)
```

## Evidence Extraction

The module automatically extracts blockchain evidence from signal metadata:

### Transaction ID Fields

The module checks multiple metadata fields for transaction IDs:
- `tx_ids`
- `transaction_ids`
- `txids`
- `transactions`

### Example

```python
signal = {
    "signal_id": "abc-123",
    "signal_type": "exchange",
    "block_height": 800000,
    "confidence": 0.85,
    "metadata": {
        "entity_name": "Coinbase",
        "transaction_ids": ["tx1", "tx2", "tx3"]  # Extracted automatically
    }
}

insight = await module.generate_insight(signal)

# Evidence includes:
# - block_heights: [800000]
# - transaction_ids: ["tx1", "tx2", "tx3"]
```

## Validation

### Signal Validation

Before processing, signals are validated for:
- Required fields: `signal_id`, `signal_type`, `block_height`, `confidence`, `metadata`
- Supported signal type (must have corresponding prompt template)

### AI Content Validation

AI-generated content is validated for:
- Headline length (max 80 characters)
- Summary length (min 10 characters)
- Confidence explanation presence

Invalid content results in `None` return value.

## Error Handling

The module handles errors gracefully:

```python
try:
    insight = await module.generate_insight(signal)
    
    if insight:
        # Success
        print(f"Generated: {insight.headline}")
    else:
        # Validation failed or AI provider error
        print("Failed to generate insight")
        
except Exception as e:
    # Unexpected error
    print(f"Error: {e}")
```

### Common Error Scenarios

1. **Invalid Signal**: Missing required fields → Returns `None`
2. **Unsupported Signal Type**: No prompt template → Returns `None`
3. **AI Provider Error**: API failure, rate limit → Returns `None`
4. **Invalid AI Content**: Headline too long, summary missing → Returns `None`

All errors are logged with context for debugging.

## Testing

### Unit Tests

Run unit tests:
```bash
cd services/insight-generator
python -m pytest tests/test_insight_generation_module.py -v
```

### Test Coverage

The test suite covers:
- ✓ Module initialization
- ✓ Signal validation (valid, missing fields, unsupported types)
- ✓ Prompt template selection (all 6 types)
- ✓ AI content validation (headline length, summary, explanation)
- ✓ Evidence extraction (tx_ids, transaction_ids, txids, duplicates)
- ✓ Insight generation (success, failures, batch processing)
- ✓ Integration with all signal types

**Test Results:** 25 tests, 100% pass rate

### Example Test

```python
@pytest.mark.asyncio
async def test_generate_insight_success(insight_module, sample_signal):
    """Test successful insight generation"""
    insight = await insight_module.generate_insight(sample_signal)
    
    assert insight is not None
    assert insight.signal_id == sample_signal["signal_id"]
    assert insight.category == sample_signal["signal_type"]
    assert len(insight.headline) <= 80
    assert len(insight.evidence.block_heights) >= 1
```

## Performance

### Latency Targets

- **Single insight generation**: < 3 seconds (AI provider call)
- **Batch processing**: Sequential (no parallelization yet)
- **Validation overhead**: < 10ms per signal

### Optimization Opportunities

1. **Parallel batch processing**: Process multiple signals concurrently
2. **Prompt caching**: Cache formatted prompts for similar signals
3. **AI response caching**: Cache responses for identical signals (testing only)

## Configuration

### Environment Variables

The module uses AI provider configuration from environment:

```bash
# AI Provider Selection
AI_PROVIDER=vertex_ai  # vertex_ai|openai|anthropic|grok

# Vertex AI
VERTEX_AI_PROJECT=utxoiq-dev
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-pro

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus-20240229

# Grok
GROK_API_KEY=xai-...
GROK_MODEL=grok-beta
```

## Integration Points

### Upstream (Input)

- **SignalPollingModule**: Provides unprocessed signals from BigQuery
- **BigQuery intel.signals**: Source of signal data

### Downstream (Output)

- **InsightPersistenceModule**: Persists generated insights to BigQuery
- **BigQuery intel.insights**: Destination for insight records

### Dependencies

- **AIProvider**: Abstract interface for AI providers (Vertex AI, OpenAI, etc.)
- **Prompt Templates**: Signal-type-specific prompt templates

## Monitoring

### Key Metrics

- Insights generated per minute
- AI provider latency (by provider)
- Validation failure rate
- Error rate by error type

### Logging

All operations are logged with structured context:

```python
logger.info(
    "Generated insight",
    extra={
        "insight_id": insight.insight_id,
        "signal_id": signal.signal_id,
        "category": signal.signal_type
    }
)
```

## Future Enhancements

### Phase 2

1. **Parallel batch processing**: Use asyncio.gather() for concurrent generation
2. **Insight quality scoring**: Add quality metrics beyond confidence
3. **Multi-signal insights**: Combine multiple signals into single insight
4. **Insight caching**: Cache insights for duplicate signals

### Phase 3

1. **Custom prompt templates**: User-defined templates
2. **Insight personalization**: Tailor insights to user preferences
3. **A/B testing**: Compare different prompt strategies
4. **Feedback loop**: Learn from user reactions

## Troubleshooting

### Issue: No insights generated

**Possible causes:**
1. Invalid signal data → Check signal validation
2. AI provider not configured → Check AI_PROVIDER env var
3. AI provider API error → Check provider logs
4. Confidence threshold too high → Check signal confidence scores

### Issue: Invalid AI content

**Possible causes:**
1. Prompt template issues → Review template formatting
2. AI provider returning wrong format → Check provider response parsing
3. Metadata missing required fields → Verify signal metadata

### Issue: Missing transaction IDs in evidence

**Possible causes:**
1. Signal metadata doesn't include tx IDs → Check signal processor output
2. Field name mismatch → Module checks: tx_ids, transaction_ids, txids, transactions

## References

- [Design Document](.kiro/specs/signal-insight-pipeline/design.md)
- [Requirements Document](.kiro/specs/signal-insight-pipeline/requirements.md)
- [AI Provider Module](./AI_PROVIDER_GUIDE.md)
- [Signal Polling Module](./SIGNAL_POLLING_MODULE.md)
