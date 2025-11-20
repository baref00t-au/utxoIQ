# Insight Generator Service

AI-powered Bitcoin blockchain insight generation service with multi-provider support, explainability, and feedback loop.

## Overview

The Insight Generator service transforms raw blockchain signals into human-readable insights using multiple AI providers (Vertex AI, OpenAI, Anthropic, xAI Grok). It includes:

- **Prompt Templates**: Context-aware prompts for each signal type (mempool, exchange, miner, whale, predictive)
- **Confidence Scoring**: Multi-factor confidence calculation with 0.7 publication threshold
- **Explainability**: Transparent confidence score breakdowns showing contributing factors
- **Feedback Loop**: User feedback collection for model retraining and accuracy tracking
- **Quiet Mode**: Automatic insight suppression during data anomalies

## Features

### AI Provider Module
- **Multi-Provider Support**: Switch between Vertex AI, OpenAI, Anthropic, and xAI Grok
- **Unified Interface**: Abstract base class for consistent behavior across providers
- **Environment Configuration**: Change providers without code changes
- **Factory Pattern**: Easy provider instantiation and management
- **Comprehensive Error Handling**: Graceful failures with detailed logging
- **See**: [AI_PROVIDER_GUIDE.md](./AI_PROVIDER_GUIDE.md) for complete documentation

### Signal Polling Module
- **BigQuery Integration**: Polls intel.signals for unprocessed signals
- **Confidence Filtering**: Only processes signals with confidence ≥ 0.7
- **Signal Grouping**: Groups signals by type and block height for batch processing
- **State Management**: Marks signals as processed after insight generation
- **Stale Signal Detection**: Identifies signals stuck in queue for alerting
- **See**: [SIGNAL_POLLING_MODULE.md](./SIGNAL_POLLING_MODULE.md) for complete documentation

### Insight Generation Module
- **Template Selection**: Chooses appropriate prompt based on signal type
- **AI Integration**: Invokes configured AI provider with formatted prompts
- **Response Validation**: Parses and validates AI-generated content
- **Evidence Extraction**: Extracts blockchain citations from signal metadata
- **Batch Processing**: Generates multiple insights efficiently
- **See**: [INSIGHT_GENERATION_MODULE.md](./INSIGHT_GENERATION_MODULE.md) for complete documentation

### Insight Persistence Module (NEW)
- **BigQuery Storage**: Writes insights to intel.insights table
- **Error Handling**: Automatic retry mechanism for failed operations
- **Batch Operations**: Efficient multi-insight persistence
- **Query Utilities**: Verification and debugging tools
- **Chart URL Management**: Sets chart_url to null for later population
- **See**: [INSIGHT_PERSISTENCE_MODULE.md](./INSIGHT_PERSISTENCE_MODULE.md) for complete documentation

### Insight Generation (Legacy)
- Generates headlines (max 280 characters for X posts)
- Creates 2-3 sentence summaries explaining significance
- Includes blockchain evidence citations (block heights, transaction IDs)
- Attaches chart URLs for visual representation
- Tags insights with relevant categories

### Confidence Scoring
- **Signal Strength** (40% weight): Measures deviation from historical patterns
- **Historical Accuracy** (35% weight): Past performance of similar signals
- **Data Quality** (25% weight): Completeness and freshness of blockchain data
- **Anomaly Detection**: Reduces confidence during mempool spikes or reorgs

### Explainability
- Breaks down confidence score into contributing factors
- Provides human-readable explanations
- Lists supporting evidence from blockchain data
- Consistent language across all insight types

### Feedback Processing
- Stores user ratings (useful/not_useful) in BigQuery
- Calculates aggregate accuracy ratings per insight
- Tracks model accuracy by version and signal type
- Generates public accuracy leaderboard
- Collects data for model retraining

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Insight Generator                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Prompt     │───▶│  Vertex AI   │───▶│   Headline   │ │
│  │  Templates   │    │  (Gemini)    │    │  Generator   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Confidence  │───▶│Explainability│───▶│   Citation   │ │
│  │   Scorer     │    │  Generator   │    │  Formatter   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Feedback Processor (BigQuery)               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.11+
- Google Cloud Platform account with Vertex AI enabled
- BigQuery datasets: `intel.insights`, `intel.user_feedback`

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your GCP credentials
```

3. Set up GCP authentication:
```bash
gcloud auth application-default login
```

## Usage

### Running the Service

```bash
# Development
uvicorn src.main:app --reload --port 8080

# Production
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

### API Endpoints

#### Generate Insight
```bash
POST /generate
Content-Type: application/json

{
  "signal_data": {
    "block_height": 800000,
    "signal_strength": 0.85,
    "change_24h": 50.0,
    "is_anomaly": false,
    "transaction_ids": ["tx1", "tx2"],
    "entity_ids": []
  },
  "signal_type": "mempool",
  "chart_url": "https://example.com/chart.png"
}
```

#### Submit Feedback
```bash
POST /feedback
Content-Type: application/json

{
  "insight_id": "insight-123",
  "user_id": "user-456",
  "rating": "useful",
  "comment": "Great insight!"
}
```

#### Get Accuracy Rating
```bash
GET /insights/{insight_id}/accuracy
```

#### Get Model Accuracy
```bash
GET /models/{model_version}/accuracy?signal_type=mempool&days=30
```

#### Get Accuracy Leaderboard
```bash
GET /leaderboard?limit=10&days=30
```

## Testing

### Run Unit Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_confidence_scorer.py -v
```

### Test Coverage

The test suite covers:
- ✅ Prompt template formatting for all signal types
- ✅ Confidence scoring algorithms
- ✅ Quiet mode detection (mempool spikes, reorgs)
- ✅ Explainability generation
- ✅ Feedback processing and aggregation
- ✅ Headline generation and validation
- ✅ Citation formatting
- ✅ End-to-end insight generation

## Configuration

### Environment Variables

```bash
# Google Cloud
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1

# BigQuery
BIGQUERY_DATASET_INTEL=intel
BIGQUERY_DATASET_BTC=btc

# Service
SERVICE_NAME=insight-generator
LOG_LEVEL=INFO
MODEL_VERSION=1.0.0

# Thresholds
CONFIDENCE_THRESHOLD=0.7
HEADLINE_MAX_LENGTH=280

# AI Provider Configuration (NEW)
# Choose one: vertex_ai, openai, anthropic, grok
AI_PROVIDER=vertex_ai

# Vertex AI (if AI_PROVIDER=vertex_ai)
VERTEX_AI_PROJECT=your-project-id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-pro

# OpenAI (if AI_PROVIDER=openai)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo

# Anthropic (if AI_PROVIDER=anthropic)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus-20240229

# xAI Grok (if AI_PROVIDER=grok)
GROK_API_KEY=xai-...
GROK_MODEL=grok-beta
GROK_API_BASE=https://api.x.ai/v1
```

## Signal Types

### Mempool
- Monitors fee quantiles and block inclusion estimates
- Detects mempool spikes exceeding 3 standard deviations
- Tracks 24-hour fee changes

### Exchange
- Detects exchange inflow spikes using entity-tagged anomaly detection
- Tracks standard deviation multiples
- Identifies unusual flow patterns

### Miner
- Tracks daily miner treasury balance changes per entity
- Monitors accumulation vs distribution trends
- Compares to 30-day averages

### Whale
- Identifies whale accumulation streaks over rolling 7-day periods
- Tracks accumulation rates
- Monitors large wallet movements

### Predictive
- Generates "Next Block Fee Forecast" using temporal models
- Computes "Exchange Liquidity Pressure Index"
- Includes confidence intervals and model accuracy

## Confidence Scoring

### Calculation Formula

```
confidence = (
    signal_strength * 0.40 +
    historical_accuracy * 0.35 +
    data_quality * 0.25
)

if is_anomaly:
    confidence *= 0.80  # 20% penalty
```

### Publication Threshold

- **≥ 0.85**: High confidence (auto-publish)
- **0.70-0.84**: Medium confidence (auto-publish)
- **< 0.70**: Low confidence (do not publish)

### Quiet Mode Triggers

- Mempool fee change > 300%
- Mempool spike > 3 standard deviations
- Blockchain reorganization detected
- Data quality < 0.5

## Explainability

Each insight includes an explainability summary with:

1. **Main Explanation**: 2-3 sentences describing why the confidence score was assigned
2. **Confidence Factors**: Breakdown of signal strength, historical accuracy, and data quality
3. **Supporting Evidence**: 3-5 bullet points with specific blockchain data

Example:
```json
{
  "explanation": "This insight has high confidence (88%) based primarily on a strong signal strength (90%). The mempool fees changed 50% in 24 hours, significantly above the historical average.",
  "confidence_factors": {
    "signal_strength": 0.90,
    "historical_accuracy": 0.82,
    "data_quality": 0.95
  },
  "supporting_evidence": [
    "Strong mempool signal detected with 90% strength",
    "Mempool fees changed 50.0% in 24 hours",
    "Historical accuracy of 82% for mempool signals",
    "High-quality blockchain data with complete transaction records",
    "Signal confirmed at block height 800000"
  ]
}
```

## Feedback Loop

### User Feedback Collection

Users can rate insights as "useful" or "not_useful" with optional comments. Feedback is stored in BigQuery for:

1. **Aggregate Accuracy Ratings**: Displayed on insight cards
2. **Model Retraining**: Collected for improving confidence scoring
3. **Public Leaderboard**: Tracks accuracy by model version
4. **Performance Monitoring**: Identifies underperforming signal types

### Accuracy Metrics

- **Insight Accuracy**: Percentage of "useful" ratings per insight
- **Model Accuracy**: Aggregate accuracy by model version and signal type
- **Leaderboard**: Public ranking of model versions by accuracy

## Deployment

### Docker

```bash
# Build image
docker build -t utxoiq-insight-generator .

# Run container
docker run -p 8080:8080 \
  -e GCP_PROJECT_ID=your-project \
  -e VERTEX_AI_MODEL=gemini-pro \
  utxoiq-insight-generator
```

### Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy insight-generator \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=your-project
```

## Monitoring

### Key Metrics

- **Insight Generation Rate**: Insights generated per hour
- **Confidence Distribution**: Percentage of high/medium/low confidence insights
- **Publication Rate**: Percentage of insights published (≥ 0.7 confidence)
- **Quiet Mode Frequency**: How often quiet mode is triggered
- **Feedback Rate**: Percentage of insights receiving user feedback
- **Model Accuracy**: Aggregate accuracy by model version

### Logging

All operations are logged with structured logging:
- Insight generation attempts
- Confidence score calculations
- Quiet mode activations
- Feedback submissions
- API requests and errors

## Requirements

See `requirements.txt` for full dependency list. Key dependencies:

- **fastapi**: Web framework
- **pydantic**: Data validation
- **google-cloud-aiplatform**: Vertex AI integration
- **google-cloud-bigquery**: Feedback storage
- **pytest**: Testing framework

## License

Proprietary - utxoIQ Platform


## FastAPI Application (NEW)

The service now runs as a FastAPI application with automatic background polling.

### Application Structure

- **Lifespan Management**: Starts/stops background polling task automatically
- **Background Polling**: Polls for unprocessed signals every 10 seconds
- **Health Checks**: `/health` endpoint for monitoring
- **Manual Triggers**: `/trigger-cycle` endpoint for testing
- **Statistics**: `/stats` endpoint for service metrics

### Running the Application

```bash
# Development with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

# Production
uvicorn src.main:app --host 0.0.0.0 --port 8080 --workers 1

# With environment variables
PORT=8080 POLL_INTERVAL_SECONDS=10 uvicorn src.main:app
```

### API Endpoints

#### GET /
Service information and status.

```bash
curl http://localhost:8080/
```

Response:
```json
{
  "service": "utxoIQ Insight Generator",
  "version": "1.0.0",
  "status": "running"
}
```

#### GET /health
Health check with service diagnostics.

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "polling_active": true,
  "poll_interval_seconds": 10,
  "confidence_threshold": 0.7,
  "ai_provider": "VertexAIProvider",
  "unprocessed_signals": 5,
  "project_id": "utxoiq-dev",
  "dataset": "intel"
}
```

#### POST /trigger-cycle
Manually trigger a polling cycle.

```bash
curl -X POST http://localhost:8080/trigger-cycle
```

Response:
```json
{
  "correlation_id": "abc-123-def-456",
  "signal_groups": 2,
  "signals_processed": 5,
  "insights_generated": 4
}
```

#### GET /stats
Get service statistics.

```bash
curl http://localhost:8080/stats
```

Response:
```json
{
  "unprocessed_signals": 10,
  "stale_signals": 2,
  "polling_active": true,
  "poll_interval_seconds": 10
}
```

### Polling Loop

The service automatically starts a background polling loop that:

1. Polls BigQuery for unprocessed signals every 10 seconds
2. Groups signals by type and block height
3. Generates insights using configured AI provider
4. Persists insights to BigQuery
5. Marks signals as processed
6. Logs all operations with correlation IDs

### Configuration

```bash
# Polling interval (seconds)
POLL_INTERVAL_SECONDS=10

# Minimum confidence threshold
CONFIDENCE_THRESHOLD=0.7

# BigQuery dataset
DATASET_INTEL=intel

# AI provider
AI_PROVIDER=vertex_ai
```

### Monitoring

The application logs all operations with correlation IDs for request tracing:

```
2024-01-15 10:30:00 - INFO - Starting polling cycle [correlation_id=abc-123]
2024-01-15 10:30:01 - INFO - Found 5 unprocessed signals
2024-01-15 10:30:02 - INFO - Generating insight for signal xyz [correlation_id=abc-123]
2024-01-15 10:30:05 - INFO - Successfully persisted insight [insight_id=def-456]
2024-01-15 10:30:05 - INFO - Polling cycle complete: 5 signals, 4 insights
```

### Requirements Implemented

This FastAPI application implements the following requirements:

- **3.1**: Poll for unprocessed signals with confidence >= 0.7
- **3.2**: Group signals by type and block height
- **3.5**: Mark signals as processed after successful insight creation
- **5.2**: Wire together all insight generation components with correlation ID logging
