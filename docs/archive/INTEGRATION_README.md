# Platform Integration - Complete Guide

## 🎯 What We Built

A **unified dashboard** that brings together all utxoIQ platform components with:
- ✅ Real-time system monitoring
- ✅ Backfill progress tracking
- ✅ User feedback system
- ✅ Live WebSocket updates
- ✅ Comprehensive metrics

## 🚀 Quick Start

### 1. Start All Services
```bash
docker-compose up -d
```

### 2. Open Dashboard
```bash
open http://localhost:3000/dashboard
```

### 3. Run Backfill (Optional)
```bash
python scripts/backfill-with-progress.py --start 800000 --end 850000
```

## 📁 Files Created

### Backend Services
```
services/web-api/src/
├── routes/
│   ├── monitoring.py          # System monitoring endpoints
│   └── feedback.py            # User feedback endpoints
└── websocket/
    └── monitoring.py          # WebSocket handler for real-time updates
```

### Frontend Components
```
frontend/src/
├── components/
│   ├── dashboard/
│   │   └── system-status.tsx  # System status dashboard
│   ├── insights/
│   │   └── insight-feedback.tsx # Feedback component
│   └── ui/
│       └── textarea.tsx       # Textarea UI component
├── app/
│   └── dashboard/
│       └── page.tsx           # Unified dashboard page
└── hooks/
    └── use-monitoring-websocket.ts # WebSocket React hook
```

### Scripts
```
scripts/
├── backfill-simple.py         # Basic backfill script
└── backfill-with-progress.py  # Enhanced backfill with progress tracking
```

### Documentation
```
docs/
├── unified-platform-integration.md  # Comprehensive guide
├── integration-summary.md           # Quick summary
├── integration-diagram.md           # Visual diagrams
├── quick-reference.md               # Quick reference
└── INTEGRATION_README.md            # This file
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Dashboard                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Insights   │  │System Status │  │   Metrics    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────────┬─────────────────────────────┘
                            │ WebSocket + REST
┌───────────────────────────▼─────────────────────────────┐
│                       Web API                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Monitoring  │  │   Feedback   │  │  WebSocket   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                   Backend Services                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Feature Engine│  │   Insight    │  │    Data      │  │
│  │              │  │  Generator   │  │  Ingestion   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                    Data Storage                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  PostgreSQL  │  │   BigQuery   │  │    Redis     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 🔌 API Endpoints

### Monitoring
- `GET /api/v1/monitoring/status` - System status
- `GET /api/v1/monitoring/backfill` - Backfill jobs
- `GET /api/v1/monitoring/metrics/signals` - Signal metrics
- `GET /api/v1/monitoring/metrics/insights` - Insight metrics

### Feedback
- `POST /api/v1/feedback/insights/{id}/rate` - Rate insight
- `POST /api/v1/feedback/insights/{id}/comment` - Comment
- `POST /api/v1/feedback/insights/{id}/flag` - Flag for review
- `GET /api/v1/feedback/insights/{id}/stats` - Feedback stats

### WebSocket
- `WS /ws/monitoring` - Real-time monitoring
- `WS /ws/insights` - Real-time insights

## 📊 Dashboard Features

### System Status Tab
- Overall system health indicator
- Individual service status (feature-engine, insight-generator, etc.)
- Backfill progress with ETA
- Processing metrics (24h blocks, insights, signals)
- Performance metrics (avg processing times)
- Live WebSocket connection indicator

### Insights Tab
- Real-time insight feed
- User feedback (ratings, comments, flags)
- Aggregated statistics
- Toast notifications for new insights

### Metrics Tab
- Signal generation by category
- Insight generation statistics
- Confidence distribution
- Historical trends

## 🔄 Real-time Updates

### WebSocket Messages

**Status Update**
```json
{
  "type": "status_update",
  "data": { "status": "healthy", "blocks_behind": 2 },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Backfill Progress**
```json
{
  "type": "backfill_update",
  "job_id": "backfill_800000_1234567890",
  "data": { "progress_percent": 50.0, "rate_blocks_per_sec": 12.5 },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**New Insight**
```json
{
  "type": "insight_generated",
  "data": { "id": "insight_123", "headline": "...", "confidence": 0.85 },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🧪 Testing

### Test WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/monitoring');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({ type: 'subscribe' }));
```

### Test Monitoring API
```bash
curl http://localhost:8000/api/v1/monitoring/status | jq
```

### Test Feedback API
```bash
curl -X POST http://localhost:8000/api/v1/feedback/insights/test123/rate \
  -H "Content-Type: application/json" \
  -d '{"rating": 5, "comment": "Great insight!"}'
```

### Test Backfill Progress
```bash
python scripts/backfill-with-progress.py \
  --start 800000 \
  --end 800010 \
  --api-url http://localhost:8000
```

## 🎨 UI Components

### System Status Dashboard
```typescript
import { SystemStatusDashboard } from '@/components/dashboard/system-status';

<SystemStatusDashboard />
```

### Insight Feedback
```typescript
import { InsightFeedback } from '@/components/insights/insight-feedback';

<InsightFeedback insightId="insight_123" />
```

### WebSocket Hook
```typescript
import { useMonitoringWebSocket } from '@/hooks/use-monitoring-websocket';

const { isConnected, lastMessage } = useMonitoringWebSocket({
  enabled: true,
  onInsightGenerated: (data) => toast.success('New insight!'),
});
```

## 🗄️ Database Schema

### Backfill Jobs
```sql
CREATE TABLE backfill_jobs (
  job_id VARCHAR(255) PRIMARY KEY,
  status VARCHAR(50) NOT NULL,
  start_block INTEGER NOT NULL,
  end_block INTEGER NOT NULL,
  current_block INTEGER NOT NULL,
  progress_percent FLOAT NOT NULL,
  rate_blocks_per_sec FLOAT NOT NULL,
  estimated_completion TIMESTAMP,
  started_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

### Insight Feedback
```sql
CREATE TABLE insight_feedback (
  id SERIAL PRIMARY KEY,
  insight_id VARCHAR(255) NOT NULL,
  user_id VARCHAR(255) NOT NULL,
  feedback_type VARCHAR(50) NOT NULL,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  flag_reason VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);
```

## 🚢 Deployment

### Docker Compose (Local)
```bash
docker-compose up -d
```

### Cloud Run (Production)
```bash
# Deploy API
gcloud run deploy utxoiq-api --source ./services/web-api

# Deploy Frontend
gcloud run deploy utxoiq-frontend --source ./frontend
```

## 📚 Documentation

- **[Comprehensive Guide](./unified-platform-integration.md)** - Full integration details
- **[Quick Summary](./integration-summary.md)** - Overview and key features
- **[Architecture Diagrams](./integration-diagram.md)** - Visual architecture
- **[Quick Reference](./quick-reference.md)** - Commands and endpoints

## 🔧 Configuration

### Backend Environment
```bash
API_URL=http://localhost:8000
DATABASE_URL=postgresql://user:pass@localhost:5432/utxoiq
BIGQUERY_PROJECT_ID=utxoiq-project
BITCOIN_RPC_URL=http://localhost:8332
REDIS_URL=redis://localhost:6379
```

### Frontend Environment
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_ENABLE_FEEDBACK=true
NEXT_PUBLIC_ENABLE_MONITORING=true
```

## 🎯 Key Benefits

1. **Unified View** - All platform components in one dashboard
2. **Real-time Updates** - No manual refresh needed
3. **Progress Tracking** - Monitor backfill and processing live
4. **User Feedback** - Collect ratings and improve insights
5. **System Health** - Proactive monitoring and alerting
6. **Developer Experience** - Easy to extend and customize

## 🔮 Future Enhancements

- [ ] Advanced filtering and search
- [ ] User preferences and customization
- [ ] Analytics dashboard with charts
- [ ] Collaborative features (sharing, comments)
- [ ] Mobile app with push notifications
- [ ] Historical trend analysis
- [ ] Alert configuration UI
- [ ] Performance optimization dashboard

## 🐛 Troubleshooting

### WebSocket Not Connecting
1. Check API is running: `curl http://localhost:8000/health`
2. Verify WebSocket URL in frontend env
3. Check browser console for errors
4. Ensure CORS is configured

### Backfill Progress Not Updating
1. Verify API URL in backfill script
2. Check API logs: `docker-compose logs web-api`
3. Test progress endpoint manually
4. Ensure database is accessible

### Frontend Not Updating
1. Check browser console for errors
2. Verify WebSocket connection in Network tab
3. Clear cache and reload (Ctrl+Shift+R)
4. Check TanStack Query devtools

## 📞 Support

- **Documentation**: See files in `docs/` directory
- **GitHub Issues**: https://github.com/utxoiq/utxoiq/issues
- **Email**: support@utxoiq.com

## ✅ Checklist

- [x] Backend monitoring endpoints
- [x] Backend feedback endpoints
- [x] WebSocket real-time updates
- [x] Frontend dashboard page
- [x] System status component
- [x] Feedback component
- [x] WebSocket React hook
- [x] Enhanced backfill script
- [x] Comprehensive documentation
- [ ] Database migrations
- [ ] Unit tests
- [ ] Integration tests
- [ ] E2E tests
- [ ] Production deployment

---

**Ready to use!** Start the services and open http://localhost:3000/dashboard
