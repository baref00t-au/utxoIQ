# Firebase Multi-Environment Setup

## Project Architecture

### Firebase Project (Single)
- **Project ID**: `utxoiq`
- **Purpose**: Authentication for ALL environments (dev, staging, prod)
- **Project Number**: `736762852981`

### Google Cloud Projects (Multiple)

#### Development/Staging
- **Project ID**: `utxoiq-dev`
- **Purpose**: Development and staging infrastructure
- **Services**: Cloud Run, BigQuery, Cloud SQL, Redis, etc.
- **Domains**: 
  - `dev.utxoiq.com` (development)
  - `staging.utxoiq.com` (staging)

#### Production
- **Project ID**: `utxoiq`
- **Purpose**: Production infrastructure
- **Services**: Cloud Run, BigQuery, Cloud SQL, Redis, etc.
- **Domains**:
  - `utxoiq.com` (production frontend)
  - `api.utxoiq.com` (production API)
  - `www.utxoiq.com` (production www)

## Why This Architecture?

### Single Firebase Project Benefits
✅ **Unified user base** - Users can access dev/staging/prod with same credentials
✅ **Simplified auth management** - One place to manage OAuth providers
✅ **Consistent user IDs** - Same Firebase UID across all environments
✅ **Cost effective** - No need for multiple Firebase projects

### Separate GCP Projects Benefits
✅ **Resource isolation** - Dev issues don't affect production
✅ **Cost tracking** - Separate billing for dev vs prod
✅ **Security boundaries** - Different IAM permissions per environment
✅ **Independent scaling** - Scale prod without affecting dev

## Configuration by Environment

### Development Environment

**GCP Project**: `utxoiq-dev`
**Firebase Project**: `utxoiq`
**Domain**: `dev.utxoiq.com`

**Backend (`services/web-api/.env.dev`):**
```bash
# Server
ENVIRONMENT=development

# Firebase Auth (shared across all environments)
FIREBASE_PROJECT_ID=utxoiq
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# Google Cloud (dev infrastructure)
GCP_PROJECT_ID=utxoiq-dev
BIGQUERY_DATASET_BTC=btc
BIGQUERY_DATASET_INTEL=intel

# Cloud SQL (dev database)
CLOUD_SQL_CONNECTION_NAME=utxoiq-dev:us-central1:utxoiq-db
DB_USER=utxoiq
DB_PASSWORD=dev_password
DB_NAME=utxoiq_db

# Redis (dev)
REDIS_HOST=10.0.0.3
REDIS_PORT=6379

# CORS
CORS_ORIGINS=http://localhost:3000,https://dev.utxoiq.com

# Stripe (test mode)
STRIPE_SECRET_KEY=sk_test_...
```

**Frontend (`frontend/.env.development`):**
```bash
# Firebase (shared)
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=utxoiq.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq

# API (dev infrastructure)
NEXT_PUBLIC_API_URL=https://dev-api.utxoiq.com

# Environment
NODE_ENV=development
```

### Staging Environment

**GCP Project**: `utxoiq-dev`
**Firebase Project**: `utxoiq`
**Domain**: `staging.utxoiq.com`

**Backend (`services/web-api/.env.staging`):**
```bash
# Server
ENVIRONMENT=staging

# Firebase Auth (shared)
FIREBASE_PROJECT_ID=utxoiq
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# Google Cloud (dev infrastructure, staging namespace)
GCP_PROJECT_ID=utxoiq-dev
BIGQUERY_DATASET_BTC=btc_staging
BIGQUERY_DATASET_INTEL=intel_staging

# Cloud SQL (staging database)
CLOUD_SQL_CONNECTION_NAME=utxoiq-dev:us-central1:utxoiq-db-staging
DB_USER=utxoiq
DB_PASSWORD=staging_password
DB_NAME=utxoiq_staging

# CORS
CORS_ORIGINS=https://staging.utxoiq.com

# Stripe (test mode)
STRIPE_SECRET_KEY=sk_test_...
```

**Frontend (`frontend/.env.staging`):**
```bash
# Firebase (shared)
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=utxoiq.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq

# API (staging infrastructure)
NEXT_PUBLIC_API_URL=https://staging-api.utxoiq.com

# Environment
NODE_ENV=production
```

### Production Environment

**GCP Project**: `utxoiq`
**Firebase Project**: `utxoiq`
**Domain**: `utxoiq.com`

**Backend (`services/web-api/.env.production`):**
```bash
# Server
ENVIRONMENT=production

# Firebase Auth (shared)
FIREBASE_PROJECT_ID=utxoiq
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# Google Cloud (prod infrastructure)
GCP_PROJECT_ID=utxoiq
BIGQUERY_DATASET_BTC=btc
BIGQUERY_DATASET_INTEL=intel

# Cloud SQL (prod database)
CLOUD_SQL_CONNECTION_NAME=utxoiq:us-central1:utxoiq-db
DB_USER=utxoiq
DB_PASSWORD=prod_password_from_secret_manager
DB_NAME=utxoiq_db

# Redis (prod)
REDIS_HOST=10.1.0.3
REDIS_PORT=6379

# CORS
CORS_ORIGINS=https://utxoiq.com,https://www.utxoiq.com

# Stripe (live mode)
STRIPE_SECRET_KEY=sk_live_...
```

**Frontend (`frontend/.env.production`):**
```bash
# Firebase (shared)
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=utxoiq.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=utxoiq

# API (prod infrastructure)
NEXT_PUBLIC_API_URL=https://api.utxoiq.com

# Environment
NODE_ENV=production
```

## Firebase Authorized Domains

Since you have ONE Firebase project for all environments, add ALL domains:

**Firebase Console** → **Authentication** → **Settings** → **Authorized domains**

```
localhost (default)
utxoiq.firebaseapp.com (default)
dev.utxoiq.com
dev-api.utxoiq.com
staging.utxoiq.com
staging-api.utxoiq.com
utxoiq.com
api.utxoiq.com
www.utxoiq.com
```

## OAuth Provider Configuration

### Google OAuth

Since Firebase Auth is shared, you need ONE set of OAuth credentials that work for all environments.

**Google Cloud Console** → **APIs & Services** → **Credentials**

**Select Project**: `utxoiq` (the Firebase project)

**Authorized redirect URIs** (add all environments):
```
# Development
http://localhost:3000/__/auth/handler
https://dev.utxoiq.com/__/auth/handler

# Staging
https://staging.utxoiq.com/__/auth/handler

# Production
https://utxoiq.com/__/auth/handler
https://www.utxoiq.com/__/auth/handler

# Firebase default
https://utxoiq.firebaseapp.com/__/auth/handler
```

### GitHub OAuth

GitHub OAuth apps only support ONE callback URL per app. You have two options:

#### Option 1: Multiple OAuth Apps (Recommended)

Create separate GitHub OAuth apps for each environment:

**Development App:**
- Name: `utxoIQ Development`
- Homepage: `https://dev.utxoiq.com`
- Callback: `https://dev.utxoiq.com/__/auth/handler`

**Staging App:**
- Name: `utxoIQ Staging`
- Homepage: `https://staging.utxoiq.com`
- Callback: `https://staging.utxoiq.com/__/auth/handler`

**Production App:**
- Name: `utxoIQ`
- Homepage: `https://utxoiq.com`
- Callback: `https://utxoiq.com/__/auth/handler`

Then in **Firebase Console** → **Authentication** → **Sign-in method** → **GitHub**:
- You can only configure ONE GitHub app at a time
- For dev/staging: Use dev GitHub app credentials
- For production: Use production GitHub app credentials
- **Problem**: This means you need to manually switch in Firebase Console

#### Option 2: Dynamic Redirect (Better)

Use Firebase's default callback URL for all environments:
- Callback: `https://utxoiq.firebaseapp.com/__/auth/handler`
- Firebase will handle redirecting back to the correct domain
- Configure this ONE callback URL in your GitHub OAuth app

## Deployment Commands

### Deploy to Development (utxoiq-dev)

```bash
# Set GCP project
gcloud config set project utxoiq-dev

# Deploy backend
cd services/web-api
gcloud run deploy utxoiq-api-dev \
  --source . \
  --region=us-central1 \
  --env-vars-file=.env.dev

# Map domain
gcloud run domain-mappings create \
  --service=utxoiq-api-dev \
  --domain=dev-api.utxoiq.com \
  --region=us-central1

# Deploy frontend
cd ../../frontend
gcloud run deploy utxoiq-frontend-dev \
  --source . \
  --region=us-central1 \
  --env-vars-file=.env.development

# Map domain
gcloud run domain-mappings create \
  --service=utxoiq-frontend-dev \
  --domain=dev.utxoiq.com \
  --region=us-central1
```

### Deploy to Staging (utxoiq-dev)

```bash
# Set GCP project
gcloud config set project utxoiq-dev

# Deploy backend
cd services/web-api
gcloud run deploy utxoiq-api-staging \
  --source . \
  --region=us-central1 \
  --env-vars-file=.env.staging

# Map domain
gcloud run domain-mappings create \
  --service=utxoiq-api-staging \
  --domain=staging-api.utxoiq.com \
  --region=us-central1

# Deploy frontend
cd ../../frontend
gcloud run deploy utxoiq-frontend-staging \
  --source . \
  --region=us-central1 \
  --env-vars-file=.env.staging

# Map domain
gcloud run domain-mappings create \
  --service=utxoiq-frontend-staging \
  --domain=staging.utxoiq.com \
  --region=us-central1
```

### Deploy to Production (utxoiq)

```bash
# Set GCP project
gcloud config set project utxoiq

# Deploy backend
cd services/web-api
gcloud run deploy utxoiq-api \
  --source . \
  --region=us-central1 \
  --env-vars-file=.env.production

# Map domain
gcloud run domain-mappings create \
  --service=utxoiq-api \
  --domain=api.utxoiq.com \
  --region=us-central1

# Deploy frontend
cd ../../frontend
gcloud run deploy utxoiq-frontend \
  --source . \
  --region=us-central1 \
  --env-vars-file=.env.production

# Map domain
gcloud run domain-mappings create \
  --service=utxoiq-frontend \
  --domain=utxoiq.com \
  --region=us-central1
```

## Service Account Credentials

### Firebase Admin SDK Credentials

You need the SAME `firebase-credentials.json` file in ALL environments since you're using one Firebase project.

**Download once:**
1. Firebase Console → Project Settings → Service Accounts
2. Generate new private key
3. Save as `firebase-credentials.json`

**Use in all environments:**
- Development: `services/web-api/firebase-credentials.json`
- Staging: Same file, deployed to Cloud Run
- Production: Same file, stored in Secret Manager

**Production Secret Manager:**
```bash
# Store in production GCP project
gcloud secrets create firebase-credentials \
  --data-file=services/web-api/firebase-credentials.json \
  --project=utxoiq

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding firebase-credentials \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=utxoiq
```

**Development Secret Manager:**
```bash
# Store in dev GCP project (same file!)
gcloud secrets create firebase-credentials \
  --data-file=services/web-api/firebase-credentials.json \
  --project=utxoiq-dev

# Grant access
gcloud secrets add-iam-policy-binding firebase-credentials \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=utxoiq-dev
```

## User Database Considerations

### Shared Firebase UIDs

Since all environments use the same Firebase project, users have the SAME Firebase UID across environments.

**Your Cloud SQL databases should:**

```sql
-- Development database (utxoiq-dev project)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,  -- Same UID as prod!
    email VARCHAR(255),
    subscription_tier VARCHAR(20) DEFAULT 'free',
    -- ... other fields
);

-- Production database (utxoiq project)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,  -- Same UID as dev!
    email VARCHAR(255),
    subscription_tier VARCHAR(20) DEFAULT 'free',
    -- ... other fields
);
```

**Important**: A user who signs up in dev will have the same Firebase UID in production, but they'll have DIFFERENT records in each database (different `id` UUID).

### Testing Considerations

**For testing, you might want:**
1. Test users in Firebase (e.g., `test@utxoiq.com`)
2. Separate test data in dev database
3. Production database only has real users

## DNS Configuration

### Development Domains (utxoiq-dev project)

```
Type: A
Name: dev.utxoiq.com
Value: [Cloud Run IP from utxoiq-dev]

Type: A
Name: dev-api.utxoiq.com
Value: [Cloud Run IP from utxoiq-dev]
```

### Staging Domains (utxoiq-dev project)

```
Type: A
Name: staging.utxoiq.com
Value: [Cloud Run IP from utxoiq-dev]

Type: A
Name: staging-api.utxoiq.com
Value: [Cloud Run IP from utxoiq-dev]
```

### Production Domains (utxoiq project)

```
Type: A
Name: utxoiq.com
Value: [Cloud Run IP from utxoiq]

Type: A
Name: api.utxoiq.com
Value: [Cloud Run IP from utxoiq]

Type: CNAME
Name: www.utxoiq.com
Value: utxoiq.com
```

## Testing Authentication Across Environments

### Test Flow

1. **Sign up in dev**: `https://dev.utxoiq.com`
   - Creates Firebase user (UID: `abc123`)
   - Creates record in dev database

2. **Sign in to staging**: `https://staging.utxoiq.com`
   - Uses same Firebase user (UID: `abc123`)
   - Creates NEW record in staging database (different UUID)

3. **Sign in to production**: `https://utxoiq.com`
   - Uses same Firebase user (UID: `abc123`)
   - Creates NEW record in production database (different UUID)

### Verify Token Works Across Environments

```bash
# Get token from dev frontend
TOKEN="eyJhbGc..."

# Test dev API
curl https://dev-api.utxoiq.com/api/v1/auth/profile \
  -H "Authorization: Bearer $TOKEN"

# Test staging API (same token works!)
curl https://staging-api.utxoiq.com/api/v1/auth/profile \
  -H "Authorization: Bearer $TOKEN"

# Test prod API (same token works!)
curl https://api.utxoiq.com/api/v1/auth/profile \
  -H "Authorization: Bearer $TOKEN"
```

## Summary

**Single Firebase Project (`utxoiq`):**
- ✅ Handles authentication for ALL environments
- ✅ One set of OAuth providers
- ✅ Shared user identities (Firebase UIDs)
- ✅ All domains authorized in one place

**Multiple GCP Projects:**
- ✅ `utxoiq-dev`: Development and staging infrastructure
- ✅ `utxoiq`: Production infrastructure
- ✅ Separate databases, separate resources
- ✅ Independent scaling and billing

**Key Insight**: Firebase Auth is just the identity provider. Your application infrastructure (databases, APIs, etc.) is completely separate per environment.
