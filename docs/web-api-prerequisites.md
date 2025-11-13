# Web API Deployment Prerequisites

## Why Deployment Failed

The web-api service failed to start because it requires several infrastructure components that aren't set up yet:

```
ERROR: The user-provided container failed to start and listen on the port
```

**Root cause**: Web-API tries to connect to Cloud SQL database on startup, but no database exists yet.

## Required Infrastructure

### 1. Cloud SQL (PostgreSQL) ✅ **REQUIRED**

**Purpose**: Store user data, alerts, subscriptions, bookmarks

**Setup**:
```bash
# Create Cloud SQL instance
gcloud sql instances create utxoiq-db-dev \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=CHANGE_ME \
  --project=utxoiq-dev

# Create database
gcloud sql databases create utxoiq \
  --instance=utxoiq-db-dev \
  --project=utxoiq-dev

# Create user
gcloud sql users create utxoiq-user \
  --instance=utxoiq-db-dev \
  --password=CHANGE_ME \
  --project=utxoiq-dev
```

**Cost**: ~$10/month (db-f1-micro)

### 2. Redis (Memorystore) ⚠️ **OPTIONAL** (for rate limiting)

**Purpose**: Rate limiting, caching

**Setup**:
```bash
# Create Redis instance
gcloud redis instances create utxoiq-redis-dev \
  --size=1 \
  --region=us-central1 \
  --tier=basic \
  --project=utxoiq-dev
```

**Cost**: ~$5/month (1GB basic tier)

**Workaround**: Can disable rate limiting for dev

### 3. Firebase Admin Credentials ✅ **REQUIRED**

**Purpose**: Validate user authentication tokens

**Setup**:
1. Go to Firebase Console → Project Settings → Service Accounts
2. Click "Generate new private key"
3. Save as `services/web-api/firebase-credentials.json`
4. Upload to Secret Manager:
   ```bash
   gcloud secrets create firebase-admin-key \
     --data-file=services/web-api/firebase-credentials.json \
     --project=utxoiq-dev
   ```

**Cost**: Free

### 4. BigQuery Dataset ✅ **ALREADY EXISTS**

**Purpose**: Read blockchain insights

**Status**: Already set up (btc, intel datasets)

**Cost**: Pay per query

## Simplified Deployment Options

### Option A: Full Setup (Recommended for Production)

Set up all infrastructure, then deploy:

**Time**: 2-3 hours
**Cost**: ~$30/month
**Benefits**: Full functionality

### Option B: Minimal Setup (Quick Start) ⬅️ **RECOMMENDED FOR NOW**

Deploy with minimal dependencies:

1. **Set up Cloud SQL only** (required)
2. **Skip Redis** (disable rate limiting)
3. **Use Firebase credentials from file**
4. **Deploy with reduced features**

**Time**: 30 minutes
**Cost**: ~$10/month
**Benefits**: Get API running quickly

### Option C: Mock Mode (Development Only)

Create a mock/dev mode that doesn't require database:

**Time**: 1 hour (code changes needed)
**Cost**: $0
**Benefits**: Fastest to test
**Drawbacks**: Limited functionality

## Recommended Next Steps

### Quick Path (Option B):

1. **Set up Cloud SQL**:
   ```bash
   scripts\setup-cloud-sql.bat dev
   ```

2. **Add Firebase credentials**:
   - Download from Firebase Console
   - Save to `services/web-api/firebase-credentials.json`

3. **Deploy with database connection**:
   ```bash
   scripts\deploy-web-api.bat dev
   ```

4. **Test**:
   ```bash
   curl https://utxoiq-web-api-dev-xxx.run.app/health
   ```

### Alternative: Use Existing utxoiq-ingestion Pattern

The `utxoiq-ingestion` service is already deployed and working. We could:

1. **Extend utxoiq-ingestion** to include API endpoints
2. **Keep it simple** - one service instead of two
3. **Add web-api features gradually**

**Pros**:
- Already deployed and working
- No new infrastructure needed
- Simpler architecture

**Cons**:
- Mixing concerns (ingestion + API)
- Less scalable long-term

## What Would You Like to Do?

### Option 1: Set Up Cloud SQL (30 min)
I'll create a script to set up Cloud SQL, then we can deploy web-api properly.

### Option 2: Extend utxoiq-ingestion (15 min)
Add API endpoints to the existing ingestion service for now.

### Option 3: Continue with Mock Data
Keep using mock data in frontend, deploy web-api later when ready for production.

## My Recommendation

For development right now:
- ✅ **Keep using mock data in frontend**
- ✅ **Focus on UI/UX development**
- ✅ **Set up infrastructure when ready for production**

This lets you:
- Continue building features
- No infrastructure costs yet
- Deploy everything together later

When ready for production:
- Set up all infrastructure properly
- Deploy web-api with full features
- Deploy frontend
- Go live

**What would you prefer?**
