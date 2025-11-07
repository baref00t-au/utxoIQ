# utxoIQ Python SDK

Official Python SDK for the utxoIQ Bitcoin blockchain intelligence platform.

## Installation

```bash
pip install utxoiq
```

## Quick Start

### Authentication with Firebase Auth

```python
from utxoiq import UtxoIQClient

# Initialize with Firebase Auth token
client = UtxoIQClient(
    firebase_token="your-firebase-jwt-token"
)

# Get latest insights
insights = client.insights.get_latest(limit=10)
for insight in insights:
    print(f"{insight.headline} (confidence: {insight.confidence})")
```

### Authentication with API Key

```python
from utxoiq import UtxoIQClient

# Initialize with API key
client = UtxoIQClient(
    api_key="your-api-key"
)

# Get specific insight
insight = client.insights.get_by_id("insight-id-123")
print(insight.summary)
```

## Features

- **Type-safe API client** with full type hints
- **Automatic retry logic** with exponential backoff
- **Firebase Auth and API key support**
- **Comprehensive error handling**
- **Pydantic models** for data validation

## Usage Examples

### Get Latest Insights

```python
# Get latest insights with filtering
insights = client.insights.get_latest(
    limit=20,
    category="mempool",
    min_confidence=0.7
)
```

### Access Daily Brief

```python
from datetime import date

# Get daily brief for specific date
brief = client.daily_brief.get_by_date(date(2025, 11, 7))
print(f"Top events: {len(brief.insights)}")
```

### Manage Alerts

```python
# Create a new alert
alert = client.alerts.create(
    signal_type="mempool",
    threshold=100.0,
    operator="gt",
    notification_channel="email"
)

# List user alerts
alerts = client.alerts.list()

# Update alert
client.alerts.update(alert.id, is_active=False)

# Delete alert
client.alerts.delete(alert.id)
```

### Submit Feedback

```python
# Rate an insight
client.feedback.submit(
    insight_id="insight-123",
    rating="useful",
    comment="Very helpful analysis"
)

# Get accuracy leaderboard
leaderboard = client.feedback.get_accuracy_leaderboard()
```

### AI Chat Queries

```python
# Ask natural language questions
response = client.chat.query(
    question="What are the current mempool fee rates?"
)
print(response.answer)
```

### Guest Mode (Public Access)

```python
# Access public insights without authentication
client = UtxoIQClient()  # No auth required
public_insights = client.insights.get_public(limit=20)
```

## Error Handling

```python
from utxoiq.exceptions import (
    UtxoIQError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)

try:
    insights = client.insights.get_latest()
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after: {e.retry_after}")
except ValidationError as e:
    print(f"Invalid request: {e}")
except UtxoIQError as e:
    print(f"API error: {e}")
```

## Configuration

### Custom Base URL

```python
client = UtxoIQClient(
    api_key="your-api-key",
    base_url="https://custom-api.utxoiq.com"
)
```

### Request Timeout

```python
client = UtxoIQClient(
    api_key="your-api-key",
    timeout=30  # seconds
)
```

### Retry Configuration

```python
client = UtxoIQClient(
    api_key="your-api-key",
    max_retries=3,
    retry_backoff_factor=2.0
)
```

## API Reference

Full API documentation is available at [https://docs.utxoiq.com/python-sdk](https://docs.utxoiq.com/python-sdk)

## Requirements

- Python 3.9+
- requests >= 2.31.0
- pydantic >= 2.5.0

## License

Proprietary - See LICENSE file for details

## Support

- Documentation: https://docs.utxoiq.com
- Email: api@utxoiq.com
- Issues: https://github.com/utxoiq/python-sdk/issues
