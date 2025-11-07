# Chart Renderer Service

AI-powered chart generation service for utxoIQ blockchain insights. Generates mobile-optimized PNG charts for mempool, exchange, miner, whale, and predictive signals.

## Features

- **Signal-specific charts**: Mempool fee distribution, exchange flows, miner treasury, whale accumulation, predictive forecasts
- **Mobile optimization**: Responsive chart sizing with 16:6 aspect ratio
- **Brand consistency**: Dark theme with utxoIQ color palette
- **Cloud Storage**: Automatic upload to GCS with signed URLs
- **High quality**: 2x pixel density for crisp rendering

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GCS credentials

# Run locally
uvicorn src.main:app --reload --port 8080

# Run tests
pytest
```

## API Endpoints

### POST /render/mempool
Generate mempool fee distribution chart with quantile visualization.

### POST /render/exchange
Generate exchange flow chart with timeline and volume indicators.

### POST /render/miner
Generate miner treasury chart with balance change visualization.

### POST /render/whale
Generate whale accumulation chart with streak highlighting.

### POST /render/predictive
Generate predictive signal chart with confidence intervals.

### GET /health
Health check endpoint.

## Chart Specifications

- **Aspect Ratio**: 16:6 for inline display
- **Mobile Width**: 800px (400px @2x)
- **Desktop Width**: 1200px (600px @2x)
- **DPI**: 150 for crisp rendering
- **Format**: PNG with compression
- **Theme**: Dark background with brand colors

## Deployment

```bash
# Build container
docker build -t chart-renderer .

# Deploy to Cloud Run
gcloud run deploy chart-renderer \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```
