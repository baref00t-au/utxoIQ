# Email Service

Email service for utxoIQ platform that handles Daily Brief delivery, email preference management, and engagement tracking.

## Features

- **Daily Brief Delivery**: Automated email delivery at 07:00 UTC
- **Preference Management**: User-configurable email preferences
- **Responsive Templates**: Mobile-optimized HTML email templates
- **Engagement Tracking**: Open rates, click-through tracking via SendGrid webhooks
- **Unsubscribe Management**: Compliant unsubscribe functionality
- **Signal Filtering**: Users can filter insights by signal type
- **Quiet Hours**: Configurable quiet hours to prevent emails during specific times

## Architecture

### Components

- **FastAPI Application**: REST API for preference management and email sending
- **SendGrid Integration**: Email delivery and engagement tracking
- **BigQuery Storage**: Email preferences and engagement data
- **Jinja2 Templates**: Responsive HTML email templates
- **API Client**: Fetches daily briefs from Web API

### Data Models

- **EmailPreferences**: User email preferences (frequency, filters, quiet hours)
- **DailyBrief**: Daily brief content with insights
- **EmailEngagement**: Engagement tracking (opens, clicks, bounces)

## Setup

### Prerequisites

- Python 3.11+
- SendGrid API key
- GCP project with BigQuery enabled
- Access to Web API for fetching daily briefs

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=noreply@utxoiq.com
SENDGRID_FROM_NAME=utxoIQ

# BigQuery Configuration
GCP_PROJECT_ID=your_gcp_project_id
BIGQUERY_DATASET=intel

# Web API Configuration
WEB_API_URL=http://localhost:8000
WEB_API_KEY=your_api_key

# Service Configuration
SERVICE_PORT=8080
LOG_LEVEL=INFO

# Frontend URL
FRONTEND_URL=https://utxoiq.com
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m uvicorn src.main:app --reload --port 8080
```

### Docker

```bash
# Build image
docker build -t utxoiq-email-service .

# Run container
docker run -p 8080:8080 --env-file .env utxoiq-email-service
```

## API Endpoints

### Health Check

```
GET /health
```

Returns service health status.

### Preference Management

```
POST /preferences/{user_id}
```

Update email preferences for a user.

**Request Body:**
```json
{
  "daily_brief_enabled": true,
  "frequency": "daily",
  "signal_filters": ["mempool", "exchange"],
  "quiet_hours": {
    "start": "22:00",
    "end": "08:00"
  }
}
```

```
GET /preferences/{user_id}
```

Get email preferences for a user.

### Unsubscribe

```
POST /unsubscribe
```

Unsubscribe a user from all emails.

**Request Body:**
```json
{
  "user_id": "user123",
  "reason": "Too many emails"
}
```

### Send Daily Brief

```
POST /send-daily-brief?date=2025-11-06
```

Trigger daily brief sending (typically called by Cloud Scheduler).

```
POST /send-daily-brief/sync?date=2025-11-06
```

Synchronously send daily briefs (for testing).

### Webhook

```
POST /webhook/sendgrid
```

Handle SendGrid webhook events for engagement tracking.

### Engagement Stats

```
GET /stats/engagement?user_id=user123&days=30
```

Get email engagement statistics.

## Email Templates

### Daily Brief Template

Responsive HTML template with:
- Dark theme matching utxoIQ brand
- Mobile-optimized layout
- Insight cards with charts
- Confidence badges
- Evidence citations
- Unsubscribe links

### Plain Text Version

Plain text fallback for email clients that don't support HTML.

## Scheduled Delivery

### Cloud Scheduler Configuration

Create a Cloud Scheduler job to trigger daily brief sending at 07:00 UTC:

```bash
gcloud scheduler jobs create http daily-brief-sender \
  --schedule="0 7 * * *" \
  --uri="https://email-service-url/send-daily-brief" \
  --http-method=POST \
  --time-zone="UTC" \
  --description="Send daily briefs at 07:00 UTC"
```

## SendGrid Webhook Setup

Configure SendGrid to send webhook events to:

```
https://your-email-service-url/webhook/sendgrid
```

Enable events:
- Delivered
- Opened
- Clicked
- Bounced
- Unsubscribed

## BigQuery Tables

### email_preferences

Stores user email preferences:
- `user_id` (STRING): User identifier
- `email` (STRING): User email address
- `daily_brief_enabled` (BOOLEAN): Whether daily briefs are enabled
- `frequency` (STRING): Email frequency (daily, weekly, never)
- `signal_filters_json` (STRING): JSON array of signal type filters
- `quiet_hours_json` (STRING): JSON object with quiet hours config
- `created_at` (TIMESTAMP): Creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### email_engagement

Tracks email engagement events:
- `email_id` (STRING): Unique email identifier
- `user_id` (STRING): User identifier
- `event` (STRING): Event type (delivered, opened, clicked, bounced, unsubscribed)
- `timestamp` (TIMESTAMP): Event timestamp
- `metadata_json` (STRING): Additional event metadata

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_email_service.py
```

## Deployment

### Cloud Run Deployment

```bash
# Build and deploy
gcloud run deploy email-service \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars SENDGRID_API_KEY=$SENDGRID_API_KEY,GCP_PROJECT_ID=$GCP_PROJECT_ID
```

## Monitoring

- Monitor email delivery rates in SendGrid dashboard
- Track engagement metrics in BigQuery
- Use Cloud Monitoring for service health
- Set up alerts for failed deliveries

## Compliance

- **CAN-SPAM Compliance**: Includes unsubscribe links in all emails
- **GDPR Compliance**: Users can manage preferences and unsubscribe
- **Privacy**: Email addresses stored securely in BigQuery
- **Opt-in**: Users must explicitly enable email preferences

## Requirements

See `requirements.txt` for full list of dependencies.

Key dependencies:
- FastAPI: Web framework
- SendGrid: Email delivery
- Jinja2: Template rendering
- google-cloud-bigquery: Data storage
- httpx: API client

## License

Proprietary - utxoIQ Platform
