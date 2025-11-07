# utxoIQ Infrastructure Setup

This directory contains infrastructure configuration and setup scripts for the utxoIQ platform.

## Prerequisites

- Google Cloud SDK (`gcloud` CLI)
- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.9+
- PostgreSQL client tools

## Local Development Setup

### 1. Start Local Services

Start PostgreSQL, Redis, and emulators using Docker Compose:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379
- BigQuery emulator on port 9050
- Cloud Pub/Sub emulator on port 8085

### 2. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Initialize Databases

The PostgreSQL database will be automatically initialized with the schema from `infrastructure/postgres/init.sql`.

To verify:

```bash
docker exec -it utxoiq-postgres psql -U utxoiq -d utxoiq_db -c "\dt"
```

### 4. Install Dependencies

Install shared module dependencies:

```bash
cd shared
npm install
```

## GCP Production Setup

### 1. Enable Required Services

```bash
gcloud services enable \
  bigquery.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com \
  cloudfunctions.googleapis.com \
  storage-api.googleapis.com \
  sql-component.googleapis.com \
  redis.googleapis.com \
  aiplatform.googleapis.com
```

### 2. Create BigQuery Datasets and Tables

Run the BigQuery setup script:

```bash
cd infrastructure/bigquery
chmod +x setup.sh
./setup.sh
```

This creates:
- `btc` dataset for raw blockchain data
- `intel` dataset for processed intelligence
- Tables with partitioning and clustering optimizations

### 3. Create Cloud Pub/Sub Topics

```bash
gcloud pubsub topics create btc.blocks
gcloud pubsub topics create btc.transactions
gcloud pubsub topics create btc.mempool
gcloud pubsub topics create insight-generated
```

### 4. Create Cloud Storage Buckets

```bash
# Charts bucket
gsutil mb -l US gs://utxoiq-charts
gsutil iam ch allUsers:objectViewer gs://utxoiq-charts

# Assets bucket
gsutil mb -l US gs://utxoiq-assets
gsutil iam ch allUsers:objectViewer gs://utxoiq-assets
```

### 5. Set Up Cloud CDN

```bash
# Create backend bucket for Cloud CDN
gcloud compute backend-buckets create utxoiq-cdn-backend \
  --gcs-bucket-name=utxoiq-charts \
  --enable-cdn

# Create URL map
gcloud compute url-maps create utxoiq-cdn-map \
  --default-backend-bucket=utxoiq-cdn-backend

# Create target HTTP proxy
gcloud compute target-http-proxies create utxoiq-cdn-proxy \
  --url-map=utxoiq-cdn-map

# Create forwarding rule
gcloud compute forwarding-rules create utxoiq-cdn-rule \
  --global \
  --target-http-proxy=utxoiq-cdn-proxy \
  --ports=80
```

### 6. Create Cloud SQL Instance

```bash
gcloud sql instances create utxoiq-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create utxoiq_db --instance=utxoiq-postgres

# Create user
gcloud sql users create utxoiq \
  --instance=utxoiq-postgres \
  --password=YOUR_SECURE_PASSWORD
```

### 7. Create Redis Instance

```bash
gcloud redis instances create utxoiq-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

## Database Schema

### BigQuery Tables

#### btc.blocks
- Partitioned by: `timestamp` (daily)
- Clustered by: `height`
- Purpose: Raw Bitcoin block data

#### intel.signals
- Partitioned by: `processed_at` (daily)
- Clustered by: `type`, `block_height`
- Purpose: Computed blockchain signals

#### intel.insights
- Partitioned by: `created_at` (daily)
- Clustered by: `signal_type`, `confidence`
- Purpose: AI-generated insights

#### intel.user_feedback
- Partitioned by: `timestamp` (daily)
- Clustered by: `insight_id`, `user_id`
- Purpose: User feedback for model improvement

### PostgreSQL Tables

- `users` - User accounts
- `user_alerts` - Custom alert configurations
- `alert_history` - Alert trigger history
- `api_keys` - API access keys
- `subscriptions` - Stripe subscription data
- `email_preferences` - Email notification settings
- `white_label_clients` - Enterprise white-label configurations

## Monitoring

### Check Service Health

```bash
# PostgreSQL
docker exec -it utxoiq-postgres pg_isready

# Redis
docker exec -it utxoiq-redis redis-cli ping

# BigQuery emulator
curl http://localhost:9050

# Pub/Sub emulator
curl http://localhost:8085
```

### View Logs

```bash
# Docker logs
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
```

## Cleanup

### Stop Local Services

```bash
docker-compose down
```

### Remove Volumes

```bash
docker-compose down -v
```

## Troubleshooting

### PostgreSQL Connection Issues

If you can't connect to PostgreSQL:

```bash
# Check if container is running
docker ps | grep postgres

# Check logs
docker logs utxoiq-postgres

# Restart container
docker-compose restart postgres
```

### BigQuery Emulator Issues

The BigQuery emulator is for local testing only. For production, use actual BigQuery.

### Port Conflicts

If ports are already in use, modify the port mappings in `docker-compose.yml`.

## Next Steps

After infrastructure setup:

1. Implement Bitcoin Core node integration (Task 1.2)
2. Set up backend services (Tasks 2-5)
3. Build frontend application (Task 6)
4. Configure monitoring and observability (Task 10)
