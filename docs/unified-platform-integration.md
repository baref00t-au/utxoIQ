# Unified Platform Integration

## Overview

This document describes the comprehensive integration of all utxoIQ platform components into a unified dashboard with real-time monitoring, feedback, and progress tracking.

## Architecture

### Components Integrated

1. **Backend Services**
   - Feature Engine (signal computation)
   - Insight Generator (AI insights)
   - Data Ingestion (blockchain data)
   - Web API (unified API layer)

2. **Frontend Dashboard**
   - System Status Monitoring
   - Backfill Progress Tracking
   - Insights Feed with Feedback
   - Real-time Metrics

3. **Real-time Communication**
   - WebSocket connections for live updates
   - Automatic query invalidation
   - Toast notifications for events

4. **Data Flow**
   - Backfill scripts report progress to API
   - Services publish events via WebSocket
   - Frontend receives real-time updates
   - Users provide feedback on insights

## API Endpoints

### Monitoring Endpoints

#### GET `/api/v1/monitoring/status`
Get overall system status including services, backfill jobs, and metrics.

**Response:**
```json
{
  "status": "healthy",
  "services": [
    {
      "name": "feature-engine",
      "status": "healthy",
      "last_check": "2024-01-15T10:30:00Z",
      "response_time_ms": 45.2
    }
  ],
  "backfill_jobs": [
    {
      "job_id": "backfill_800000_1234567890",
      "status": "running",
      "start_block": 800000,
      "end_block": 850000,
      "current_block": 825000,
      "progress_percent": 50.0,
      "rate_blocks_per_sec": 12.5,
      "estimated_completion": "2024-01-15T12:00:00Z"
    }
  ],
  "processing_metrics": {
    "blocks_processed_24h": 144,
    "insights_generated_24h": 42,
    "signals_computed_24h": 156,
    "blocks_behind": 2
  }
}
```

#### GET `/api/v1/monitoring/backfill`
Get list of backfill jobs with optional status filter.

**Query Parameters:**
- `status`: Filter by job status (running, paused, completed, failed)
- `limit`: Maximum number of jobs to return (default: 10)

#### GET `/api/v1/monitoring/metrics/signals`
Get signal generation metrics over time.

**Query Parameters:**
- `hours`: Number of hours to look back (default: 24)

**Response:**
```json
{
  "period_hours": 24,
  "signals_by_category": {
    "mempool": 45,
    "exchange": 38,
    "miner": 42,
    "whale": 31
  },
  "signals_by_confidence": {
    "high": 67,
    "medium": 58,
    "low": 31
  },
  "total_signals": 156
}
```

#### GET `/api/v1/monitoring/metrics/insights`
Get insight generation metrics over time.

### Feedback Endpoints

#### POST `/api/v1/feedback/insights/{insight_id}/rate`
Rate an insight (1-5 stars) with optional comment.

**Request Body:**
```json
{
  "rating": 5,
  "comment": "Very accurate and helpful!"
}
```

#### POST `/api/v1/feedback/insights/{insight_id}/flag`
Flag an insight for review.

**Request Body:**
```json
{
  "reason": "inaccurate",
  "details": "The transaction count seems incorrect"
}
```

**Flag Reasons:**
- `inaccurate`: Inaccurate information
- `misleading`: Misleading content
- `spam`: Spam content
- `inappropriate`: Inappropriate content
- `other`: Other reason

#### GET `/api/v1/feedback/insights/{insight_id}/stats`
Get aggregated feedback statistics for an insight.

**Response:**
```json
{
  "insight_id": "insight_123",
  "total_ratings": 42,
  "avg_rating": 4.2,
  "rating_distribution": {
    "1": 2,
    "2": 3,
    "3": 8,
    "4": 15,
    "5": 14
  },
  "total_comments": 12,
  "total_flags": 1
}
```

## WebSocket Connections

### `/ws/monitoring`
Real-time system monitoring updates.

**Message Types:**

1. **status_update** - System status changes
```json
{
  "type": "status_update",
  "data": {
    "status": "healthy",
    "blocks_behind": 2,
    "processing_rate": 0.95
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

2. **backfill_update** - Backfill progress updates
```json
{
  "type": "backfill_update",
  "job_id": "backfill_800000_1234567890",
  "data": {
    "current_block": 825000,
    "progress_percent": 50.0,
    "rate_blocks_per_sec": 12.5
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

3. **insight_generated** - New insight created
```json
{
  "type": "insight_generated",
  "data": {
    "id": "insight_123",
    "headline": "Large exchange outflow detected",
    "category": "exchange",
    "confidence": 0.85
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

4. **signal_computed** - New signal computed
```json
{
  "type": "signal_computed",
  "data": {
    "id": "signal_456",
    "type": "mempool_congestion",
    "value": 0.78
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### `/ws/insights`
Real-time insight streaming (existing).

## Frontend Components

### Dashboard Page (`/dashboard`)
Unified dashboard with three tabs:
- **Insights**: Live feed of AI-generated insights
- **System Status**: Real-time monitoring and health
- **Metrics**: Signal and insight generation statistics

### System Status Dashboard
Real-time monitoring component showing:
- Overall system health
- Individual service status
- Backfill progress with ETA
- Processing metrics (24h)
- Performance metrics (avg times)
- WebSocket connection indicator

### Insight Feedback
User feedback component for insights:
- Star rating (1-5)
- Comments
- Flag/report functionality
- Aggregated statistics display

## Backfill Scripts

### `scripts/backfill-simple.py`
Basic backfill script without progress reporting.

**Usage:**
```bash
python scripts/backfill-simple.py --start 800000 --end 850000 --batch-size 100
```

### `scripts/backfill-with-progress.py`
Enhanced backfill script with API progress reporting.

**Usage:**
```bash
python scripts/backfill-with-progress.py \
  --start 800000 \
  --end 850000 \
  --batch-size 100 \
  --api-url http://localhost:8000 \
  --report-interval 10
```

**Features:**
- Creates job in API on start
- Reports progress every N batches
- Calculates ETA based on processing rate
- Marks job as completed/failed
- Handles interruptions gracefully

## React Hooks

### `useMonitoringWebSocket`
Custom hook for WebSocket monitoring connection.

**Usage:**
```typescript
const { isConnected, lastMessage } = useMonitoringWebSocket({
  enabled: true,
  onStatusUpdate: (data) => {
    console.log('Status updated:', data);
  },
  onBackfillUpdate: (jobId, data) => {
    console.log('Backfill progress:', jobId, data);
  },
  onInsightGenerated: (data) => {
    toast.success('New insight generated!');
  },
  onSignalComputed: (data) => {
    console.log('Signal computed:', data);
  },
});
```

**Features:**
- Automatic reconnection on disconnect
- Heartbeat ping/pong
- Query invalidation on updates
- Custom event handlers
- Connection status tracking

## Data Flow

### Backfill Progress Flow
```
1. User starts backfill script
2. Script creates job via API
3. Script processes blocks in batches
4. Every N batches, script reports progress to API
5. API stores progress in database
6. API broadcasts update via WebSocket
7. Frontend receives update and invalidates queries
8. Dashboard shows updated progress
9. On completion, script marks job as done
```

### Insight Generation Flow
```
1. New block processed by data-ingestion
2. Feature-engine computes signals
3. Insight-generator creates insight
4. Insight stored in database
5. API broadcasts insight_generated event
6. Frontend receives event via WebSocket
7. Toast notification shown to user
8. Insights feed automatically refreshes
9. User can rate/comment on insight
10. Feedback stored and aggregated
```

### Real-time Monitoring Flow
```
1. Frontend connects to /ws/monitoring
2. WebSocket manager accepts connection
3. Broadcast loop starts (every 5 seconds)
4. System status fetched from services
5. Status broadcast to all connected clients
6. Frontend updates dashboard in real-time
7. User sees live metrics without refresh
```

## Database Schema

### Backfill Jobs Table
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

### Insight Feedback Table
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

## Environment Variables

### Backend
```bash
# API Configuration
API_URL=http://localhost:8000
WS_URL=ws://localhost:8000

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/utxoiq
BIGQUERY_PROJECT_ID=utxoiq-project

# Bitcoin RPC
BITCOIN_RPC_URL=http://localhost:8332
BITCOIN_RPC_USER=bitcoin
BITCOIN_RPC_PASSWORD=password
```

### Frontend
```bash
# API URLs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_FEEDBACK=true
NEXT_PUBLIC_ENABLE_MONITORING=true
```

## Deployment

### Docker Compose
All services can be started together:

```bash
docker-compose up -d
```

Services included:
- web-api (port 8000)
- feature-engine (port 8001)
- insight-generator (port 8002)
- frontend (port 3000)
- postgres (port 5432)
- redis (port 6379)

### Cloud Run
Each service deploys independently:

```bash
# Deploy API
gcloud run deploy utxoiq-api --source ./services/web-api

# Deploy Frontend
gcloud run deploy utxoiq-frontend --source ./frontend
```

## Testing

### Backend Tests
```bash
# Test monitoring endpoints
pytest services/web-api/tests/test_monitoring.py

# Test feedback endpoints
pytest services/web-api/tests/test_feedback.py

# Test WebSocket
pytest services/web-api/tests/test_websocket.py
```

### Frontend Tests
```bash
# Test dashboard components
npm test -- dashboard

# Test WebSocket hook
npm test -- use-monitoring-websocket

# E2E tests
npm run test:e2e
```

### Integration Tests
```bash
# Test backfill with progress reporting
python scripts/backfill-with-progress.py --start 800000 --end 800010 --api-url http://localhost:8000

# Monitor progress in dashboard
open http://localhost:3000/dashboard
```

## Monitoring & Observability

### Metrics to Track
- Backfill processing rate (blocks/sec)
- Insight generation rate (insights/hour)
- Signal computation rate (signals/hour)
- API response times
- WebSocket connection count
- User feedback submission rate

### Alerts
- System status degraded/down
- Blocks behind > 10
- Backfill job failed
- High error rate in processing
- WebSocket connection failures

## Future Enhancements

1. **Advanced Filtering**
   - Filter insights by category, confidence, date range
   - Search insights by keywords
   - Bookmark favorite insights

2. **User Preferences**
   - Customize dashboard layout
   - Set notification preferences
   - Configure alert thresholds

3. **Analytics Dashboard**
   - Historical trends and charts
   - Performance comparisons
   - User engagement metrics

4. **Collaborative Features**
   - Share insights with team
   - Comment threads on insights
   - Insight collections/playlists

5. **Mobile App**
   - Native iOS/Android apps
   - Push notifications
   - Offline mode

## Troubleshooting

### WebSocket Not Connecting
- Check NEXT_PUBLIC_WS_URL is correct
- Verify web-api is running
- Check browser console for errors
- Ensure CORS is configured properly

### Backfill Progress Not Updating
- Verify API_URL in backfill script
- Check API logs for errors
- Ensure database is accessible
- Verify WebSocket is broadcasting

### Feedback Not Submitting
- Check user authentication
- Verify API endpoint is accessible
- Check request payload format
- Review API logs for validation errors

## Support

For issues or questions:
- GitHub Issues: https://github.com/utxoiq/utxoiq/issues
- Documentation: https://docs.utxoiq.com
- Email: support@utxoiq.com
