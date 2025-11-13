# Deployment Strategy - Dev vs Production

## GCP Projects

### Development/Staging: `utxoiq-dev`
- For testing and development
- Lower cost configuration
- Can break things without affecting users
- Services: `*-dev` suffix

### Production: `utxoiq`
- For live users
- High availability configuration
- Monitored 24/7
- Services: no suffix

## Service Naming Convention

### Development
- `utxoiq-web-api-dev`
- `utxoiq-ingestion-dev`
- `utxoiq-frontend-dev`

### Production
- `utxoiq-web-api`
- `utxoiq-ingestion`
- `utxoiq-frontend`

## Deployment Commands

### Deploy to Development

```bash
# Web API
scripts\deploy-web-api.bat dev

# Ingestion Service
scripts\deploy-ingestion.bat dev

# Frontend
scripts\deploy-frontend.bat dev
```

### Deploy to Production

```bash
# Web API
scripts\deploy-web-api.bat prod

# Ingestion Service
scripts\deploy-ingestion.bat prod

# Frontend
scripts\deploy-frontend.bat prod
```

## Environment Variables by Environment

### Development (`utxoiq-dev`)

```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=https://utxoiq-web-api-dev-xxx.us-central1.run.app
NEXT_PUBLIC_WS_URL=wss://utxoiq-web-api-dev-xxx.us-central1.run.app
NEXT_PUBLIC_USE_MOCK_DATA=false
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq

# Backend
ENVIRONMENT=development
GCP_PROJECT_ID=utxoiq-dev
FIREBASE_PROJECT_ID=utxoiq
```

### Production (`utxoiq`)

```bash
# Frontend (.env.production)
NEXT_PUBLIC_API_URL=https://api.utxoiq.com
NEXT_PUBLIC_WS_URL=wss://api.utxoiq.com
NEXT_PUBLIC_USE_MOCK_DATA=false
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq

# Backend
ENVIRONMENT=production
GCP_PROJECT_ID=utxoiq
FIREBASE_PROJECT_ID=utxoiq
```

## Deployment Workflow

### 1. Development Cycle

```
Local Development
    ↓
Commit to Git
    ↓
Deploy to utxoiq-dev
    ↓
Test in Dev Environment
    ↓
If OK → Promote to Production
```

### 2. Production Deployment

```
Merge to main branch
    ↓
Run tests
    ↓
Deploy to utxoiq (production)
    ↓
Monitor for errors
    ↓
Rollback if needed
```

## Resource Configuration

### Development (Cost-Optimized)

```yaml
web-api-dev:
  memory: 512Mi
  cpu: 1
  min-instances: 0
  max-instances: 5
  
ingestion-dev:
  memory: 512Mi
  cpu: 1
  min-instances: 0
  max-instances: 2
```

**Estimated Cost**: $10-20/month

### Production (Performance-Optimized)

```yaml
web-api:
  memory: 1Gi
  cpu: 2
  min-instances: 1
  max-instances: 20
  
ingestion:
  memory: 1Gi
  cpu: 1
  min-instances: 1
  max-instances: 5
```

**Estimated Cost**: $50-100/month

## Database Strategy

### Development
- **Cloud SQL**: db-f1-micro (shared CPU)
- **Redis**: Basic tier, 1GB
- **BigQuery**: On-demand pricing

### Production
- **Cloud SQL**: db-n1-standard-1 (dedicated CPU)
- **Redis**: Standard tier, 5GB, HA
- **BigQuery**: Flat-rate pricing (if high volume)

## Monitoring & Alerts

### Development
- Basic Cloud Monitoring
- Email alerts for critical errors
- 7-day log retention

### Production
- Full Cloud Monitoring suite
- PagerDuty integration
- 30-day log retention
- Uptime checks every 1 minute
- SLO monitoring (99.9% uptime)

## Deployment Checklist

### Before Deploying to Production

- [ ] All tests passing
- [ ] Tested in dev environment
- [ ] Database migrations ready
- [ ] Environment variables configured
- [ ] Secrets stored in Secret Manager
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented
- [ ] Team notified

### After Deploying to Production

- [ ] Verify service is healthy
- [ ] Check logs for errors
- [ ] Test critical user flows
- [ ] Monitor metrics for 30 minutes
- [ ] Update documentation
- [ ] Notify team of completion

## Rollback Procedure

If production deployment fails:

```bash
# Rollback to previous revision
gcloud run services update-traffic utxoiq-web-api \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region us-central1 \
  --project utxoiq

# Or rollback via console
# Cloud Run → utxoiq-web-api → Revisions → Manage Traffic
```

## CI/CD Integration (Future)

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches:
      - main        # Deploy to production
      - develop     # Deploy to dev

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Dev
        if: github.ref == 'refs/heads/develop'
        run: ./scripts/deploy-web-api.sh dev
        
      - name: Deploy to Prod
        if: github.ref == 'refs/heads/main'
        run: ./scripts/deploy-web-api.sh prod
```

## Current Status

### Deployed Services

**Development (utxoiq-dev)**:
- ✅ `utxoiq-ingestion` (deployed, running)
- ❌ `utxoiq-web-api-dev` (not deployed yet)
- ❌ `utxoiq-frontend-dev` (not deployed yet)

**Production (utxoiq)**:
- ❌ No services deployed yet

### Next Steps

1. Deploy web-api to dev: `scripts\deploy-web-api.bat dev`
2. Test in dev environment
3. Deploy frontend to dev
4. Full integration testing
5. Deploy to production when ready

## Cost Comparison

| Service | Dev (utxoiq-dev) | Prod (utxoiq) |
|---------|------------------|---------------|
| Cloud Run | $10-20/mo | $50-100/mo |
| Cloud SQL | $10/mo | $50/mo |
| Redis | $5/mo | $30/mo |
| BigQuery | $5/mo | $20-50/mo |
| **Total** | **$30-40/mo** | **$150-230/mo** |

## Security Considerations

### Development
- Allow unauthenticated access (for testing)
- Relaxed CORS policies
- Debug logging enabled

### Production
- Require authentication for sensitive endpoints
- Strict CORS policies
- Error logging only (no debug logs)
- Rate limiting enforced
- DDoS protection enabled
- Regular security audits
