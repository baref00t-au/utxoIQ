# utxoIQ Web API Service

AI-powered Bitcoin blockchain intelligence platform API with WebSocket support, Firebase Auth, and comprehensive OpenAPI v3 documentation.

## Features

- **RESTful API**: Comprehensive endpoints for insights, alerts, billing, and more
- **WebSocket Streaming**: Real-time insight broadcasting with < 2 second latency
- **Firebase Authentication**: Secure user authentication with JWT tokens
- **Rate Limiting**: Redis-based rate limiting per subscription tier
- **OpenAPI v3**: Auto-generated documentation at `/docs` and `/redoc`
- **Guest Mode**: Public access to 20 recent insights without authentication
- **Subscription Tiers**: Free, Pro, Power, and White-Label tiers
- **User Feedback**: Collect and aggregate insight accuracy ratings

## Quick Start

### Prerequisites

- Python 3.11+
- Redis (for rate limiting)
- Firebase Admin SDK credentials
- Google Cloud credentials (for BigQuery, Cloud SQL)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
```

### Running Locally

```bash
# Development mode with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8080 --workers 4
```

### Docker

```bash
# Build image
docker build -t utxoiq-web-api .

# Run container
docker run -p 8080:8080 --env-file .env utxoiq-web-api
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## Endpoints

### Public Endpoints (No Auth Required)

- `GET /insights/public` - Get 20 most recent insights (Guest Mode)
- `GET /insights/latest` - Get latest insights with pagination
- `GET /insight/{id}` - Get specific insight with explainability
- `GET /daily-brief/{date}` - Get daily brief for a date
- `GET /insights/accuracy-leaderboard` - Public accuracy ratings
- `WS /ws/insights` - WebSocket for real-time insight streaming

### Authenticated Endpoints (Firebase Auth Required)

- `POST /alerts` - Create custom alert
- `GET /alerts` - Get user alerts
- `PUT /alerts/{id}` - Update alert
- `DELETE /alerts/{id}` - Delete alert
- `POST /insights/{id}/feedback` - Submit feedback
- `POST /chat/query` - AI chat query
- `GET /billing/subscription` - Get subscription info
- `GET /email/preferences` - Get email preferences
- `PUT /email/preferences` - Update email preferences

## WebSocket Usage

### JavaScript Example

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/insights?token=YOUR_FIREBASE_TOKEN');

ws.onopen = () => {
  console.log('Connected to utxoIQ real-time stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'insight') {
    console.log('New insight:', data.data);
  } else if (data.type === 'heartbeat') {
    console.log('Heartbeat received');
  }
};

// Send ping to keep connection alive
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
}, 30000);
```

### Python Example

```python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8080/ws/insights?token=YOUR_FIREBASE_TOKEN"
    
    async with websockets.connect(uri) as websocket:
        # Receive welcome message
        welcome = await websocket.recv()
        print(f"Connected: {welcome}")
        
        # Listen for insights
        async for message in websocket:
            data = json.loads(message)
            
            if data['type'] == 'insight':
                print(f"New insight: {data['data']['headline']}")
            elif data['type'] == 'heartbeat':
                print("Heartbeat received")

asyncio.run(connect())
```

## Authentication

### Firebase Auth Token

Include Firebase Auth JWT token in the `Authorization` header:

```
Authorization: Bearer YOUR_FIREBASE_JWT_TOKEN
```

### API Key (Coming Soon)

For programmatic access, use API key in header:

```
X-API-Key: YOUR_API_KEY
```

## Rate Limiting

Rate limits per subscription tier (per hour):

- **Free**: 100 requests
- **Pro**: 1,000 requests
- **Power**: 10,000 requests
- **White-Label**: 100,000 requests

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Total limit
- `X-RateLimit-Remaining`: Remaining requests
- `Retry-After`: Seconds until limit resets (when exceeded)

## Error Handling

All errors follow a standardized format:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit exceeded. Try again in 60 seconds.",
    "details": {
      "limit": 100,
      "window": "1h",
      "retry_after": 60
    }
  },
  "request_id": "req_abc123",
  "timestamp": "2025-11-07T10:30:00Z"
}
```

### Error Codes

- `DATA_UNAVAILABLE` (503): Blockchain data not yet available
- `CONFIDENCE_TOO_LOW` (422): Insight confidence below threshold
- `RATE_LIMIT_EXCEEDED` (429): Rate limit exceeded
- `SUBSCRIPTION_REQUIRED` (402): Feature requires paid subscription
- `VALIDATION_ERROR` (400): Request validation failed
- `UNAUTHORIZED` (401): Authentication required or invalid
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `INTERNAL_ERROR` (500): Server error

## Development

### Project Structure

```
services/web-api/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models/              # Pydantic models
│   ├── routes/              # API route handlers
│   ├── services/            # Business logic services
│   ├── middleware/          # Auth and rate limiting
│   └── websocket/           # WebSocket manager
├── tests/                   # Integration tests
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
└── README.md               # This file
```

### Adding New Endpoints

1. Create Pydantic models in `src/models/`
2. Create service class in `src/services/`
3. Create route handler in `src/routes/`
4. Include router in `src/main.py`

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src tests/
```

## Deployment

### Cloud Run

```bash
# Build and deploy
gcloud run deploy utxoiq-web-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### Environment Variables

See `.env.example` for required configuration.

## License

Proprietary - utxoIQ Platform
