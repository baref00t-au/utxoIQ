# Insight Generator Service

AI-powered Bitcoin blockchain insight generation service with explainability and feedback loop.

## Overview

The Insight Generator service transforms raw blockchain signals into human-readable insights using Vertex AI (Gemini Pro). It includes:

- **Prompt Templates**: Context-aware prompts for each signal type (mempool, exchange, miner, whale, predictive)
- **Confidence Scoring**: Multi-factor confidence calculation with 0.7 publication threshold
- **Explainability**: Transparent confidence score breakdowns showing contributing factors
- **Feedback Loop**: User feedback collection for model retraining and accuracy tracking
- **Quiet Mode**: Automatic insight suppression during data anomalies

## Features

### Insight Generation
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
VERTEX_AI_MODEL=gemini-pro

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
