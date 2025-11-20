# AI Provider Module Guide

## Overview

The AI Provider Module provides a unified interface for generating insights using multiple AI providers:
- **Vertex AI** (Google Gemini Pro)
- **OpenAI** (GPT-4 Turbo)
- **Anthropic** (Claude 3 Opus)
- **xAI Grok** (Grok Beta)

This allows the insight-generator service to switch between providers without code changes, enabling cost optimization, redundancy, and A/B testing.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ AIProvider (Abstract Base Class)                        │
│ - generate_insight(signal, prompt_template)             │
│ - _format_prompt(signal, template)                      │
│ - _parse_json_response(response_text)                   │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│ VertexAI       │  │ OpenAI      │  │ Anthropic       │
│ Provider       │  │ Provider    │  │ Provider        │
└────────────────┘  └─────────────┘  └─────────────────┘
                            │
                    ┌───────▼────────┐
                    │ Grok           │
                    │ Provider       │
                    └────────────────┘
```

## Configuration

### Environment Variables

Set the `AI_PROVIDER` environment variable to choose your provider:

```bash
# Choose one provider
AI_PROVIDER=vertex_ai    # or openai, anthropic, grok
```

### Provider-Specific Configuration

#### Vertex AI (Default)
```bash
AI_PROVIDER=vertex_ai
VERTEX_AI_PROJECT=your-gcp-project-id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-pro
```

#### OpenAI
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo
```

#### Anthropic
```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus-20240229
```

#### xAI Grok
```bash
AI_PROVIDER=grok
GROK_API_KEY=xai-...
GROK_MODEL=grok-beta
GROK_API_BASE=https://api.x.ai/v1
```

## Installation

### Base Dependencies
```bash
pip install -r requirements.txt
```

### Provider-Specific Dependencies

Install only the provider you plan to use:

```bash
# For Vertex AI (included in base requirements)
# Already installed via google-cloud-aiplatform

# For OpenAI
pip install openai>=1.0.0

# For Anthropic
pip install anthropic>=0.18.0

# For Grok (uses httpx, already included)
# No additional installation needed
```

## Usage

### Basic Usage

```python
from ai_provider import get_configured_provider, Signal

# Get provider based on environment configuration
provider = get_configured_provider()

# Create signal
signal = Signal(
    signal_id="signal-123",
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

# Define prompt template
prompt_template = """
Analyze this mempool signal:
- Fee Rate: {fee_rate_median} sat/vB
- Change: {fee_rate_change_pct}%
- TX Count: {tx_count}

Respond with JSON containing headline, summary, confidence_explanation.
"""

# Generate insight
insight_content = await provider.generate_insight(signal, prompt_template)

print(f"Headline: {insight_content.headline}")
print(f"Summary: {insight_content.summary}")
print(f"Confidence: {insight_content.confidence_explanation}")
```

### Using Specific Provider

```python
from ai_provider import AIProviderFactory

# Create specific provider with custom config
config = {
    "api_key": "sk-test-key",
    "model": "gpt-4-turbo"
}

provider = AIProviderFactory.create_provider("openai", config)

# Use provider
insight_content = await provider.generate_insight(signal, prompt_template)
```

### Error Handling

```python
from ai_provider import get_configured_provider, AIProviderError
import logging

logger = logging.getLogger(__name__)

try:
    provider = get_configured_provider()
    insight_content = await provider.generate_insight(signal, prompt_template)
    
except AIProviderError as e:
    logger.error(
        f"AI provider failed: {e}",
        extra={"signal_id": signal.signal_id}
    )
    # Mark signal as unprocessed for retry
    # Don't switch providers - let retry handle it
    
except Exception as e:
    logger.error(
        f"Unexpected error: {e}",
        extra={"signal_id": signal.signal_id}
    )
```

## Prompt Templates

All providers expect prompts that request JSON responses with these fields:
- `headline`: Short title (max 80 characters)
- `summary`: 2-3 sentence explanation
- `confidence_explanation`: Why this signal is reliable

### Example Prompt Template

```python
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
```

## Response Format

All providers return `InsightContent` with:

```python
@dataclass
class InsightContent:
    headline: str                    # Max 80 characters
    summary: str                     # 2-3 sentences
    confidence_explanation: str      # Why signal is reliable
```

## Provider Comparison

| Provider | Model | Latency | Cost | JSON Support |
|----------|-------|---------|------|--------------|
| Vertex AI | Gemini Pro | ~2s | Low | Native |
| OpenAI | GPT-4 Turbo | ~3s | Medium | Native |
| Anthropic | Claude 3 Opus | ~2.5s | High | Via prompt |
| Grok | Grok Beta | ~2s | TBD | Native |

## Best Practices

### 1. Provider Selection
- **Vertex AI**: Best for GCP-native deployments, low cost
- **OpenAI**: Best for quality and reliability
- **Anthropic**: Best for nuanced analysis
- **Grok**: Best for real-time data integration

### 2. Error Handling
- Always catch `AIProviderError` exceptions
- Log errors with `signal_id` context
- Mark signals as unprocessed for retry
- Don't automatically switch providers on failure

### 3. Prompt Engineering
- Keep prompts concise and focused
- Use consistent JSON format across providers
- Include all necessary context in metadata
- Test prompts with each provider

### 4. Cost Optimization
- Use Vertex AI for high-volume processing
- Reserve premium providers for high-confidence signals
- Monitor API costs via Cloud Monitoring
- Implement rate limiting if needed

### 5. Testing
- Test with mock responses in unit tests
- Use dev environment for integration testing
- Compare output quality across providers
- Monitor latency and error rates

## Monitoring

### Key Metrics

Track these metrics for each provider:

```python
# Latency
ai_provider_latency_ms{provider="vertex_ai", success="true"}

# Error rate
ai_provider_errors{provider="openai", error_type="timeout"}

# Cost (if tracking enabled)
ai_provider_cost{provider="anthropic", model="claude-3-opus"}
```

### Logging

All providers log structured messages:

```python
logger.info(
    "Generating insight with Vertex AI",
    extra={"signal_id": signal.signal_id}
)

logger.error(
    "OpenAI generation failed: timeout",
    extra={"signal_id": signal.signal_id, "error": "timeout"}
)
```

## Troubleshooting

### Provider Not Found
```
AIProviderError: Invalid provider type: invalid_provider
```
**Solution**: Check `AI_PROVIDER` environment variable. Valid values: `vertex_ai`, `openai`, `anthropic`, `grok`

### Missing API Key
```
AIProviderError: OpenAI API key not provided
```
**Solution**: Set provider-specific API key environment variable (e.g., `OPENAI_API_KEY`)

### Invalid JSON Response
```
AIProviderError: Invalid JSON response: Expecting value
```
**Solution**: Check prompt template requests JSON format. Some providers need explicit JSON instructions.

### Missing Response Fields
```
AIProviderError: Missing required fields in AI response: ['summary']
```
**Solution**: Ensure prompt template requests all required fields: `headline`, `summary`, `confidence_explanation`

### Import Error
```
AIProviderError: OpenAI dependencies not installed
```
**Solution**: Install provider-specific dependencies: `pip install openai>=1.0.0`

## Testing

Run unit tests:

```bash
cd services/insight-generator
pytest tests/ai-provider.unit.test.py -v
```

Test with specific provider:

```bash
# Set environment
export AI_PROVIDER=vertex_ai
export VERTEX_AI_PROJECT=your-project

# Run tests
pytest tests/ai-provider.unit.test.py -v
```

## Migration Guide

### Switching Providers

To switch from one provider to another:

1. Install new provider dependencies (if needed)
2. Update environment variables
3. Test with sample signals
4. Deploy with new configuration
5. Monitor error rates and latency

No code changes required!

### Example: Vertex AI → OpenAI

```bash
# Before
AI_PROVIDER=vertex_ai
VERTEX_AI_PROJECT=my-project

# After
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo
```

## Future Enhancements

- **Provider fallback**: Automatically switch on failure
- **Load balancing**: Distribute requests across providers
- **A/B testing**: Compare quality across providers
- **Cost tracking**: Monitor per-provider costs
- **Custom providers**: Plugin system for new providers

## Requirements Mapping

This module satisfies the following requirements:

- **8.1**: AI provider configuration from environment
- **8.2**: Vertex AI implementation with Gemini Pro
- **8.3**: OpenAI implementation with GPT models
- **8.4**: Anthropic implementation with Claude models
- **8.5**: xAI Grok implementation
- **8.6**: Abstract provider interface
- **8.7**: Error handling without provider switching

## Support

For issues or questions:
1. Check logs for error messages with `signal_id`
2. Verify environment configuration
3. Test with sample signals
4. Review provider-specific documentation
