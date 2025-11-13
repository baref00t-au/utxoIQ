# Database Migrations Guide

## Current Status

✅ **Web API Deployed**: https://utxoiq-web-api-dev-544291059247.us-central1.run.app  
❌ **Database Tables**: Not created yet - migrations need to be run

## Problem

The web-api service is deployed and can connect to Cloud SQL, but the database tables don't exist yet. When the API tries to query the `users` table, it fails with:

```
asyncpg.exceptions.UndefinedTableError: relation "users" does not exist
```

## Solution: Run Migrations from Cloud Shell

The easiest way to run Alembic migrations against Cloud SQL is from Google Cloud Shell, which has built-in authentication and the Cloud SQL Proxy.

### Step 1: Open Cloud Shell

1. Go to https://console.cloud.google.com
2. Select project: `utxoiq-dev`
3. Click the Cloud Shell icon (>_) in the top right

### Step 2: Clone Repository (if needed)

```bash
# If not already cloned
git clone https://github.com/YOUR_USERNAME/utxoiq.git
cd utxoiq
```

### Step 3: Install Dependencies

```bash
cd services/web-api

# Install Python dependencies
pip3 install --user -r requirements.txt
```

### Step 4: Set Environment Variables

```bash
export CLOUD_SQL_CONNECTION_NAME="utxoiq-dev:us-central1:utxoiq-db-dev"
export DB_USER="postgres"
export DB_PASSWORD="utxoiq_SecurePass123!"
export DB_NAME="utxoiq"
export DB_HOST="127.0.0.1"
export DB_PORT="5432"
export ENVIRONMENT="development"
export GCP_PROJECT_ID="utxoiq-dev"
export FIREBASE_PROJECT_ID="utxoiq"
export BIGQUERY_DATASET_INTEL="intel"
export BIGQUERY_DATASET_BTC="btc"
export VERTEX_AI_LOCATION="us-central1"
export STRIPE_SECRET_KEY="sk_test_dummy"
export STRIPE_WEBHOOK_SECRET="whsec_dummy"
export CORS_ORIGINS="http://localhost:3000"
```

### Step 5: Run Migrations

```bash
# Run Alembic migrations
python3 -m alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001, create_backfill_jobs
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, create_insight_feedback
INFO  [alembic.runtime.migration] Running upgrade 002 -> 003, create_system_metrics
INFO  [alembic.runtime.migration] Running upgrade 003 -> 004, create_users_and_api_keys
INFO  [alembic.runtime.migration] Running upgrade 004 -> 005, create_alert_configurations
```

### Step 6: Verify Tables Created

```bash
# Connect to Cloud SQL
gcloud sql connect utxoiq-db-dev --user=postgres --database=utxoiq

# List tables
\dt

# Expected tables:
# - alembic_version
# - backfill_jobs
# - insight_feedback
# - system_metrics
# - users
# - api_keys
# - alert_configurations
# - alert_history

# Exit psql
\q
```

## Alternative: Run Migrations Locally with Cloud SQL Proxy

If you prefer to run migrations from your local machine:

### Step 1: Install Cloud SQL Proxy

Download from: https://cloud.google.com/sql/docs/postgres/sql-proxy

### Step 2: Start Cloud SQL Proxy

```bash
# Windows
cloud-sql-proxy utxoiq-dev:us-central1:utxoiq-db-dev

# The proxy will listen on localhost:5432
```

### Step 3: Run Migrations (in another terminal)

```bash
cd services/web-api

# Set environment variables (PowerShell)
$env:CLOUD_SQL_CONNECTION_NAME="utxoiq-dev:us-central1:utxoiq-db-dev"
$env:DB_USER="postgres"
$env:DB_PASSWORD="utxoiq_SecurePass123!"
$env:DB_NAME="utxoiq"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="5432"
# ... (set other env vars)

# Run migrations
python -m alembic upgrade head
```

## Migration Files

The following migrations will be applied:

1. **001_create_backfill_jobs.py** - Backfill job tracking
2. **002_create_insight_feedback.py** - User feedback on insights
3. **003_create_system_metrics.py** - System performance metrics
4. **004_create_users_and_api_keys.py** - User accounts and API keys
5. **005_create_alert_configurations.py** - Alert configurations and history

## After Migrations Complete

Once migrations are successful:

1. **Test the API**:
   ```bash
   curl https://utxoiq-web-api-dev-544291059247.us-central1.run.app/health
   ```

2. **Update Frontend**:
   - Set `NEXT_PUBLIC_USE_MOCK_DATA=false` in `frontend/.env.local`
   - The frontend will now use real API data

3. **Test Frontend Integration**:
   - Start Next.js dev server: `npm run dev`
   - Sign in with Google
   - Verify filter presets and other features work

## Troubleshooting

### Error: "password authentication failed"

- Verify the password is correct
- Reset password if needed:
  ```bash
  gcloud sql users set-password postgres \
    --instance=utxoiq-db-dev \
    --password="utxoiq_SecurePass123!" \
    --project=utxoiq-dev
  ```

### Error: "relation does not exist"

- Migrations haven't been run yet
- Follow the steps above to run migrations

### Error: "connection refused"

- Cloud SQL Proxy isn't running
- Start the proxy before running migrations

### Error: "module not found"

- Install missing dependencies:
  ```bash
  pip3 install --user alembic asyncpg cloud-sql-python-connector pydantic-settings
  ```

## Next Steps

After migrations are complete:

1. ✅ Create initial user accounts (via Firebase Auth + Firestore)
2. ✅ Test API endpoints with authentication
3. ✅ Verify frontend can fetch data from API
4. ✅ Set up monitoring and alerts
5. ✅ Deploy to production environment
