# X Bot Service

Automated social media posting service for utxoIQ Bitcoin blockchain insights.

## Overview

The X Bot service automatically posts high-confidence blockchain insights to X (Twitter) and generates daily "Bitcoin Pulse" summary threads. It integrates with the Web API to fetch publishable insights and uses Redis for duplicate prevention.

## Features

- **Hourly Insight Posting**: Automatically posts insights with confidence ≥ 0.7
- **Daily Bitcoin Pulse Thread**: Posts a curated thread at 07:00 UTC with top 3-5 events
- **Duplicate Prevention**: Uses Redis to prevent posting duplicate insights within 15-minute windows
- **Chart Attachments**: Automatically attaches chart images to tweets
- **Manual Posting**: API endpoints for manual insight posting

## Architecture

### Components

- **PostingService**: Manages insight composition and posting logic
- **DailyBriefService**: Handles daily thread generation and posting
- **XClient**: Wrapper for X API v2 interactions
- **RedisClient**: Manages duplicate prevention and state tracking
- **APIClient**: Fetches insights from Web API service

### Data Flow

1. Cloud Scheduler triggers hourly endpoint
2. Service fetches publishable insights from Web API
3. Filters insights based on confidence and duplicate prevention
4. Composes tweets with headlines, confidence, and block context
5. Downloads and uploads chart images
6. Posts tweets to X
7. Marks insights as posted in Redis

## Configuration

### Environment Variables

```bash
# X API Credentials
X_API_KEY=your_x_api_key
X_API_SECRET=your_x_api_secret
X_ACCESS_TOKEN=your_x_access_token
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret
X_BEARER_TOKEN=your_x_bearer_token

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# GCP Configuration
GCP_PROJECT_ID=your_project_id
GCS_BUCKET_NAME=utxoiq-charts

# API Configuration
WEB_API_URL=http://localhost:8000
WEB_API_KEY=your_api_key

# Bot Configuration
CONFIDENCE_THRESHOLD=0.7
DUPLICATE_PREVENTION_WINDOW=900
DAILY_BRIEF_TIME=07:00
HOURLY_CHECK_ENABLED=true
```

## API Endpoints

### POST /post/hourly
Triggered by Cloud Scheduler for hourly insight posting.

**Response:**
```json
{
  "status": "completed",
  "total_processed": 5,
  "successful_posts": 3,
  "failed_posts": 2,
  "results": [...]
}
```

### POST /post/daily-brief
Triggered by Cloud Scheduler for daily Bitcoin Pulse thread.

**Query Parameters:**
- `brief_date` (optional): Date in YYYY-MM-DD format

**Response:**
```json
{
  "status": "completed",
  "total_tweets": 5,
  "successful_tweets": 5,
  "failed_tweets": 0,
  "tweet_ids": ["123...", "456..."]
}
```

### POST /post/insight/{insight_id}
Manually post a specific insight.

**Response:**
```json
{
  "status": "success",
  "insight_id": "abc123",
  "tweet_id": "789..."
}
```

### GET /status/recent-posts
Get status of recent posts.

**Response:**
```json
{
  "last_daily_brief_date": "2025-11-07",
  "duplicate_prevention_window": 900,
  "confidence_threshold": 0.7
}
```

## Development

### Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment file:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. Run the service:
```bash
uvicorn src.main:app --reload --port 8080
```

### Docker Build

```bash
docker build -t utxoiq-x-bot .
docker run -p 8080:8080 --env-file .env utxoiq-x-bot
```

## Deployment

### Cloud Run Deployment

```bash
gcloud run deploy utxoiq-x-bot \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "$(cat .env | grep -v '^#' | xargs)"
```

### Cloud Scheduler Setup

**Hourly Insight Posting:**
```bash
gcloud scheduler jobs create http x-bot-hourly \
  --schedule="0 * * * *" \
  --uri="https://utxoiq-x-bot-xxx.run.app/post/hourly" \
  --http-method=POST \
  --time-zone="UTC"
```

**Daily Brief Posting:**
```bash
gcloud scheduler jobs create http x-bot-daily-brief \
  --schedule="0 7 * * *" \
  --uri="https://utxoiq-x-bot-xxx.run.app/post/daily-brief" \
  --http-method=POST \
  --time-zone="UTC"
```

## Tweet Composition

### Insight Tweet Format

```
[Headline]

🟢 Confidence: 85%
📦 Block: 820000

🔗 utxoiq.com/insight/abc123
```

### Daily Thread Format

**Intro Tweet:**
```
⚡ Bitcoin Pulse — November 7, 2025

Top 3 blockchain events from the past 24 hours:

🧵 Thread below 👇
```

**Insight Tweets:**
```
1/ 📊 MEMPOOL

Mempool fees spike to 150 sat/vB

Average fee rates increased 3x in the last hour...

Confidence: 92% | Block: 820000
```

**Outro Tweet:**
```
📱 Get real-time Bitcoin intelligence:
→ utxoiq.com

🔔 Never miss an insight — follow us for hourly updates!
```

## Duplicate Prevention

The service uses Redis to prevent duplicate posts:

- **Insight-level**: Tracks individual insights for the duplicate prevention window (15 minutes)
- **Signal-level**: Prevents posting multiple insights of the same signal type within the window
- **Daily brief**: Tracks the last posted daily brief date to prevent duplicates

## Error Handling

- Failed media uploads: Tweet posts without image
- Failed tweet posts: Logged but doesn't mark as posted
- API failures: Logged and retried on next scheduled run
- Redis failures: Logged but doesn't block posting (fail-open)

## Monitoring

Key metrics to monitor:
- Successful post rate
- Failed post rate
- Duplicate prevention hits
- API response times
- Redis connection health
- X API rate limit usage

## Testing

Run tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```
