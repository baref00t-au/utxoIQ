# Web API Service - Deployment Guide

## What is web-api?

The **web-api** service is the main backend API for utxoIQ. It's a FastAPI application that provides:

### Core Features

1. **User Authentication & Authorization**
   - Firebase Auth integration
   - JWT token validation
   - Role-based access control (RBAC)
   - API key management

2. **Insights API**
   - Get latest insights from BigQuery
   - Filter by category, confidence, date
   - Guest mode (20 public insights)
   - Insight detail with explainability

3. **User Profile Management**
   - `/api/v1/auth/profile` - Get user profile
   - Subscription tier management
   - User preferences

4. **Alerts & Notifications**
   - Create custom alerts
   - Manage alert configurations
   - Alert history
   - Email notifications

5. **Billing & Subscriptions**
   - Stripe integration
   - Subscription management
   - Usage tracking
   - Billing history

6. **Bookmarks & Collections**
   - Save favorite insights
   - Organize into folders
   - Export bookmarks

7. **Data Export**
   - Export insights to CSV/JSON
   - Custom field selection
   - Date range filtering

8. **Filter Presets**
   - Save custom filters
   - Built-in presets
   - Share presets

9. **AI Chat**
   - Natural language queries
   - Blockchain data Q&A
   - Powered by Vertex AI

10. **Real-time WebSocket**
    - Live insight streaming
    - < 2 second latency
    - Heartbeat monitoring

11. **Monitoring & Observability**
    - System health endpoints
    - Metrics collection
    - Log aggregation
    - Distributed tracing

### Why You Need It

Currently, your frontend is using:
- **Mock data** for insights
- **Firestore** for user profiles (fallback)
- **No backend API** for features like alerts, billing, chat, etc.

With web-api deployed, you'll get:
- ✅ Real insights from BigQuery
- ✅ Full user profile management
- ✅ Alerts and notifications
- ✅ Billing and subscriptions
- ✅ AI chat functionality
- ✅ Data export
- ✅ Real-time WebSocket updates

## Deployment Steps

### Prerequisites

1. **GCP Project**: utxoiq (or utxoiq-dev)
2. **Services Enabled**:
   - Cloud Run
   - Cloud SQL
   - Redis (Memorystore)
   - BigQuery
   - Secret Manager

3. **Credentials**:
   - Firebase Admin SDK key
   - Stripe API keys
   - GCP service account

### Step 1: Prepare Environment Variables

Create `.env` file in `services/web-api/`:

```bash
# Database
DATABASE_URL=postgresql://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE

# Redis
REDIS_URL=redis://10.x.x.x:6379

# Firebase
FIREBASE_PROJECT_ID=utxoiq
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# BigQuery
BIGQUERY_PROJECT_ID=utxoiq-dev
BIGQUERY_DATASET=btc

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Vertex AI
VERTEX_AI_PROJECT_ID=utxoiq-dev
VERTEX_AI_LOCATION=us-central1

# CORS
CORS_ORIGINS=https://utxoiq.com,http://localhost:3000

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Step 2: Deploy to Cloud Run

```bash
cd services/web-api

# Deploy
gcloud run deploy utxoiq-web-api \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars="ENVIRONMENT=production" \
  --set-cloudsql-instances=PROJECT:REGION:INSTANCE \
  --project utxoiq-dev
```

### Step 3: Set Up Secrets

```bash
# Store Firebase credentials
gcloud secrets create firebase-admin-key \
  --data-file=firebase-credentials.json \
  --project utxoiq-dev

# Store Stripe keys
echo -n "sk_live_..." | gcloud secrets create stripe-secret-key \
  --data-file=- \
  --project utxoiq-dev

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding firebase-admin-key \
  --member="serviceAccount:PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project utxoiq-dev
```

### Step 4: Update Frontend Configuration

Update `frontend/.env.local`:

```bash
# Change from localhost to deployed URL
NEXT_PUBLIC_API_URL=https://utxoiq-web-api-xxx.us-central1.run.app
NEXT_PUBLIC_WS_URL=wss://utxoiq-web-api-xxx.us-central1.run.app

# Disable mock data
NEXT_PUBLIC_USE_MOCK_DATA=false
```

### Step 5: Verify Deployment

```bash
# Get service URL
gcloud run services describe utxoiq-web-api \
  --region us-central1 \
  --format="value(status.url)" \
  --project utxoiq-dev

# Test health endpoint
curl https://utxoiq-web-api-xxx.us-central1.run.app/health

# Test API docs
open https://utxoiq-web-api-xxx.us-central1.run.app/docs
```

## Post-Deployment

### 1. Test Authentication

```bash
# Get Firebase token from browser console after signing in
TOKEN="your_firebase_token"

# Test profile endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://utxoiq-web-api-xxx.us-central1.run.app/api/v1/auth/profile
```

### 2. Monitor Logs

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=utxoiq-web-api" \
  --limit 50 \
  --format json \
  --project utxoiq-dev
```

### 3. Set Up Monitoring

- Go to Cloud Console → Cloud Run → utxoiq-web-api
- Check metrics: requests, latency, errors
- Set up alerts for errors and high latency

## Cost Estimate

**Cloud Run Pricing** (us-central1):
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GiB-second
- **Requests**: $0.40 per million requests

**Estimated Monthly Cost** (moderate usage):
- 100,000 requests/month
- Average 500ms response time
- 1 vCPU, 1GB memory
- **Total**: ~$10-20/month

With min-instances=0, you only pay when the service is handling requests.

## Troubleshooting

### Service won't start
- Check logs: `gcloud logging read ...`
- Verify environment variables are set
- Check Cloud SQL connection
- Verify Redis is accessible

### Authentication errors
- Verify Firebase credentials are correct
- Check CORS origins include your frontend URL
- Ensure Firebase project ID matches

### Database connection errors
- Verify Cloud SQL instance is running
- Check connection string format
- Ensure Cloud Run has Cloud SQL access
- Verify database exists and migrations ran

### Rate limiting not working
- Check Redis connection
- Verify Redis URL is correct
- Check Redis is accessible from Cloud Run

## Next Steps

After deployment:

1. **Run database migrations**:
   ```bash
   # Connect to Cloud SQL and run migrations
   ```

2. **Set up Cloud Scheduler** for cleanup jobs

3. **Configure monitoring alerts**

4. **Set up CI/CD** for automatic deployments

5. **Enable Cloud CDN** for static assets

6. **Set up custom domain** (api.utxoiq.com)

## Support

For issues:
- Check Cloud Run logs
- Review API documentation at `/docs`
- Test endpoints with `/redoc`
- Check service health at `/health`
