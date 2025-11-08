# Quick Reference Guide

## URLs

### Local Development
- **Frontend**: http://localhost:3000
- **Dashboard**: http://localhost:3000/dashboard
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/monitoring

### Production
- **Frontend**: https://utxoiq.com
- **Dashboard**: https://utxoiq.com/dashboard
- **API**: https://api.utxoiq.com
- **WebSocket**: wss://api.utxoiq.com/ws/monitoring

## Common Commands

### Start Services
```bash
# All services with Docker
docker-compose up -d

# Frontend only
cd frontend && npm run dev

# Web API only
cd services/web-api && python -m uvicorn src.main:app --reload

# Feature Engine
cd services/feature-engine && python -m uvicorn src.main:app --reload --port 8001
```

### Run Backfill
```bash
# Simple backfill
python scripts/backfill-simple.py --start 800000 --end 850000

# With progress tracking
python scripts/backfill-with-progress.py \
  --start 800000 \
  --end 850000 \
  --api-url http://localhost:8000
```

### Test APIs
```bash
# System status
curl http://localhost:8000/api/v1/monitoring/status | jq

# Backfill jobs
curl http://localhost:8000/api/v1/monitoring/backfill | jq

# Signal metrics
curl http://localhost:8000/api/v1/monitoring/metrics/signals | jq

# Rate insight
curl -X POST http://localhost:8000/api/v1/feedback/insights/test123/rate \
  -H "Content-Type: application/json" \
  -d '{"rating": 5, "comment": "Great!"}'
```

### Test WebSocket
```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws/monitoring');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({ type: 'subscribe' }));
```

## API Endpoints

### Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/monitoring/status` | Overall system status |
| GET | `/api/v1/monitoring/backfill` | List backfill jobs |
| GET | `/api/v1/monitoring/backfill/{job_id}` | Get specific job |
| GET | `/api/v1/monitoring/metrics/signals` | Signal metrics |
| GET | `/api/v1/monitoring/metrics/insights` | Insight metrics |

### Feedback
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/feedback/insights/{id}/rate` | Rate insight (1-5) |
| POST | `/api/v1/feedback/insights/{id}/comment` | Add comment |
| POST | `/api/v1/feedback/insights/{id}/flag` | Flag for review |
| GET | `/api/v1/feedback/insights/{id}/stats` | Get feedback stats |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `/ws/monitoring` | Real-time monitoring updates |
| `/ws/insights` | Real-time insight streaming |

## WebSocket Message Types

### Received from Server
```typescript
// Status update
{
  "type": "status_update",
  "data": { "status": "healthy", "blocks_behind": 2 },
  "timestamp": "2024-01-15T10:30:00Z"
}

// Backfill update
{
  "type": "backfill_update",
  "job_id": "backfill_800000_1234567890",
  "data": { "progress_percent": 50.0, "rate_blocks_per_sec": 12.5 },
  "timestamp": "2024-01-15T10:30:00Z"
}

// New insight
{
  "type": "insight_generated",
  "data": { "id": "insight_123", "headline": "...", "confidence": 0.85 },
  "timestamp": "2024-01-15T10:30:00Z"
}

// New signal
{
  "type": "signal_computed",
  "data": { "id": "signal_456", "type": "mempool_congestion", "value": 0.78 },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Send to Server
```typescript
// Subscribe to updates
{ "type": "subscribe" }

// Ping (heartbeat)
{ "type": "ping", "timestamp": "2024-01-15T10:30:00Z" }
```

## React Hooks

### useMonitoringWebSocket
```typescript
import { useMonitoringWebSocket } from '@/hooks/use-monitoring-websocket';

const { isConnected, lastMessage, send } = useMonitoringWebSocket({
  enabled: true,
  onStatusUpdate: (data) => console.log('Status:', data),
  onBackfillUpdate: (jobId, data) => console.log('Backfill:', jobId, data),
  onInsightGenerated: (data) => toast.success('New insight!'),
  onSignalComputed: (data) => console.log('Signal:', data),
});
```

## Component Usage

### System Status Dashboard
```typescript
import { SystemStatusDashboard } from '@/components/dashboard/system-status';

export default function Page() {
  return <SystemStatusDashboard />;
}
```

### Insight Feedback
```typescript
import { InsightFeedback } from '@/components/insights/insight-feedback';

export default function InsightDetail({ insightId }: { insightId: string }) {
  return (
    <div>
      <h1>Insight Details</h1>
      <InsightFeedback insightId={insightId} />
    </div>
  );
}
```

## Environment Variables

### Backend (.env)
```bash
# API
API_URL=http://localhost:8000
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/utxoiq
BIGQUERY_PROJECT_ID=utxoiq-project

# Bitcoin
BITCOIN_RPC_URL=http://localhost:8332
BITCOIN_RPC_USER=bitcoin
BITCOIN_RPC_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379

# Vertex AI
VERTEX_AI_PROJECT=utxoiq-project
VERTEX_AI_LOCATION=us-central1
```

### Frontend (.env.local)
```bash
# API URLs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_FEEDBACK=true
NEXT_PUBLIC_ENABLE_MONITORING=true
```

## Database Schema

### backfill_jobs
```sql
CREATE TABLE backfill_jobs (
  job_id VARCHAR(255) PRIMARY KEY,
  status VARCHAR(50) NOT NULL,
  start_block INTEGER NOT NULL,
  end_block INTEGER NOT NULL,
  current_block INTEGER NOT NULL,
  blocks_processed INTEGER NOT NULL,
  blocks_remaining INTEGER NOT NULL,
  progress_percent FLOAT NOT NULL,
  rate_blocks_per_sec FLOAT NOT NULL,
  estimated_completion TIMESTAMP,
  started_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  error_count INTEGER DEFAULT 0,
  error_message TEXT
);
```

### insight_feedback
```sql
CREATE TABLE insight_feedback (
  id SERIAL PRIMARY KEY,
  insight_id VARCHAR(255) NOT NULL,
  user_id VARCHAR(255) NOT NULL,
  feedback_type VARCHAR(50) NOT NULL,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  flag_reason VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(insight_id, user_id, feedback_type)
);
```

## Troubleshooting

### WebSocket Not Connecting
```bash
# Check if API is running
curl http://localhost:8000/health

# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  http://localhost:8000/ws/monitoring
```

### Backfill Not Reporting Progress
```bash
# Check API is accessible
curl http://localhost:8000/api/v1/monitoring/status

# Check logs
docker-compose logs web-api

# Test progress endpoint
curl -X POST http://localhost:8000/api/v1/monitoring/backfill \
  -H "Content-Type: application/json" \
  -d '{"job_id": "test", "status": "running", ...}'
```

### Frontend Not Updating
```bash
# Check browser console for errors
# Open DevTools > Console

# Check WebSocket connection
# Open DevTools > Network > WS

# Clear cache and reload
# Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
```

## Performance Tips

### Backend
- Use connection pooling for database
- Enable Redis caching for frequently accessed data
- Implement rate limiting per user/IP
- Use async/await for I/O operations
- Batch database writes when possible

### Frontend
- Use React.memo for expensive components
- Implement virtualization for long lists
- Lazy load components with dynamic imports
- Optimize images with Next.js Image component
- Use ISR for static content with revalidation

### WebSocket
- Implement heartbeat to detect dead connections
- Batch messages when possible
- Use binary format for large payloads
- Implement reconnection with exponential backoff
- Limit broadcast frequency (e.g., max 1/sec)

## Monitoring Checklist

- [ ] All services are healthy
- [ ] WebSocket connections are stable
- [ ] Backfill jobs are progressing
- [ ] Insights are being generated
- [ ] Signals are being computed
- [ ] User feedback is being collected
- [ ] No errors in logs
- [ ] Response times are acceptable
- [ ] Database queries are optimized
- [ ] Cache hit rate is high

## Deployment Checklist

- [ ] Environment variables are set
- [ ] Database migrations are applied
- [ ] Secrets are in Secret Manager
- [ ] CORS origins are configured
- [ ] Rate limits are set
- [ ] Health checks are passing
- [ ] Monitoring is enabled
- [ ] Alerts are configured
- [ ] Backups are scheduled
- [ ] Documentation is updated

## Support Resources

- **Documentation**: `docs/unified-platform-integration.md`
- **Architecture**: `docs/integration-diagram.md`
- **API Docs**: http://localhost:8000/docs
- **GitHub**: https://github.com/utxoiq/utxoiq
- **Email**: support@utxoiq.com
