# utxoIQ Services Architecture

## Overview

This directory contains all backend services for the utxoIQ platform. Services are organized by function and deployed independently to Google Cloud Run.

## Active Services

### 1. utxoiq-ingestion (PRIMARY - UNIFIED SERVICE)

**Purpose**: Core data pipeline - monitors blockchain, ingests blocks, processes signals

**Includes**:
- ✅ Block monitoring via Umbrel + Tor
- ✅ Automatic fallback to mempool.space API
- ✅ Block ingestion to BigQuery
- ✅ Transaction processing
- ✅ Signal generation (mempool, exchange, miner, whale)
- ✅ Predictive analytics

**Deployment**: `scripts\deploy-utxoiq-ingestion.bat`

**Status**: ACTIVE - This is the main service you should deploy

---

### 2. web-api

**Purpose**: Public REST API for frontend and external clients

**Includes**:
- User authentication (Firebase)
- Subscription management (Stripe)
- Insight retrieval
- Alert management
- Rate limiting

**Deployment**: `scripts\deploy-web-api.bat`

**Status**: ACTIVE

---

### 3. insight-generator

**Purpose**: AI-powered insight generation using Vertex AI

**Includes**:
- Gemini Pro integration
- Prompt engineering
- Confidence scoring
- Evidence citation

**Deployment**: TBD

**Status**: PLANNED

---

### 4. chart-renderer

**Purpose**: Generate chart images for insights

**Includes**:
- Chart generation
- GCS upload
- CDN integration

**Deployment**: TBD

**Status**: PLANNED

---

### 5. x-bot

**Purpose**: Social media automation for X (Twitter)

**Includes**:
- Tweet composition
- Scheduled posting
- High-confidence insight sharing

**Deployment**: TBD

**Status**: PLANNED

---

### 6. email-service

**Purpose**: Email notifications and alerts

**Includes**:
- Alert notifications
- Daily brief emails
- Transactional emails

**Deployment**: TBD

**Status**: PLANNED

---

## Deprecated/Legacy Services

### ❌ block-monitor (DEPRECATED)

**Status**: DEPRECATED - Functionality moved to utxoiq-ingestion

**Reason**: Block monitoring is now integrated into utxoiq-ingestion as a unified service. The standalone block-monitor service is no longer needed.

**Migration**: All block monitoring features are now in `utxoiq-ingestion/src/monitor/`

---

### ❌ data-ingestion (DEPRECATED)

**Status**: DEPRECATED - Replaced by utxoiq-ingestion

**Reason**: Renamed and enhanced to utxoiq-ingestion with additional features.

---

## Service Communication

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Flow                                │
└─────────────────────────────────────────────────────────────┘

Umbrel Node (.onion)
  ↓ (via Tor)
utxoiq-ingestion
  ├─ Monitors blocks
  ├─ Ingests to BigQuery
  └─ Generates signals
       ↓
BigQuery (btc.blocks, btc.transactions, intel.signals)
       ↓
web-api
  ├─ Serves frontend
  ├─ Manages users
  └─ Handles subscriptions
       ↓
Frontend (Next.js)
```

## Deployment Order

1. **utxoiq-ingestion** (FIRST - core data pipeline)
2. **web-api** (SECOND - serves frontend)
3. **insight-generator** (THIRD - AI insights)
4. **chart-renderer** (FOURTH - visualizations)
5. **x-bot** (FIFTH - social media)
6. **email-service** (SIXTH - notifications)

## Environment Configuration

Each service has:
- `.env` - Local development configuration (gitignored)
- `.env.example` - Template for configuration
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies

## Development Workflow

### Local Development

```cmd
REM 1. Set up environment
cd services\utxoiq-ingestion
copy .env.example .env
REM Edit .env with your configuration

REM 2. Install dependencies
pip install -r requirements.txt

REM 3. Run locally
python -m uvicorn src.main:app --reload --port 8080
```

### Deployment to Cloud Run

```cmd
REM Deploy utxoiq-ingestion
scripts\deploy-utxoiq-ingestion.bat

REM Deploy web-api
scripts\deploy-web-api.bat
```

## Service URLs (utxoiq-dev)

- **utxoiq-ingestion**: https://utxoiq-ingestion-544291059247.us-central1.run.app
- **web-api**: https://web-api-544291059247.us-central1.run.app

## Monitoring

### Health Checks

All services expose `/health` endpoint:
```cmd
curl https://utxoiq-ingestion-544291059247.us-central1.run.app/health
```

### Status Endpoints

Services expose `/status` for detailed status:
```cmd
curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status
```

### Logs

View service logs:
```cmd
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=utxoiq-ingestion"
```

## Cost Optimization

### Always-On Services (min-instances=1)
- **utxoiq-ingestion**: ~$32/month (critical - monitors blockchain)
- **web-api**: ~$28/month (user-facing)

### On-Demand Services (min-instances=0)
- **insight-generator**: ~$5/month (triggered by signals)
- **chart-renderer**: ~$2/month (triggered by insights)
- **x-bot**: ~$1/month (scheduled cron)
- **email-service**: ~$1/month (triggered by alerts)

**Total Estimated Cost**: ~$69/month

## Security

### Secrets Management

Sensitive configuration (RPC passwords, API keys) should be:
1. Stored in `.env` for local development (gitignored)
2. Set as Cloud Run environment variables for production
3. Use Secret Manager for highly sensitive data

### Network Security

- All services use HTTPS
- Tor for Umbrel communication
- IAM for service-to-service auth
- Rate limiting on public endpoints

## Troubleshooting

### Service Won't Start

```cmd
REM Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME" --limit 20

REM Common issues:
REM 1. Missing environment variables
REM 2. Invalid configuration
REM 3. Dependency conflicts
```

### Tor Connection Issues

```cmd
REM Test locally first
.\venv312\Scripts\python.exe scripts\test-umbrel-tor-connection.py

REM Check Tor in container
gcloud run services describe utxoiq-ingestion --region us-central1
```

### BigQuery Issues

```cmd
REM Check dataset exists
bq ls utxoiq-dev:

REM Check recent blocks
bq query --use_legacy_sql=false "SELECT MAX(number) as latest_block FROM btc.blocks"
```

## Support

For issues:
1. Check service logs
2. Verify environment configuration
3. Test locally before deploying
4. Check Cloud Run console for errors
