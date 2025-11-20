# utxoIQ Ingestion Service

The utxoIQ Ingestion Service is the core data pipeline that monitors Bitcoin blockchain, ingests blocks, and processes signals. This is a **unified service** that combines block monitoring, data ingestion, and signal processing.

## Overview

This unified service implements:

### Block Monitoring & Ingestion
- **Automatic Block Detection**: Monitors Bitcoin Core via Tor for new blocks
- **Dual Data Sources**: Primary (Umbrel via Tor) + Fallback (mempool.space API)
- **Real-time Processing**: Ingests blocks within 60 seconds of detection
- **BigQuery Storage**: Stores blocks and transactions in structured format

### Signal Processing Pipeline
- **Mempool Signal Processing**: Fee quantile calculation and block inclusion time estimation
- **Exchange Flow Detection**: Entity-tagged transaction analysis with anomaly detection
- **Miner Treasury Tracking**: Daily balance change calculation and treasury delta computation
- **Whale Accumulation Detection**: Rolling 7-day accumulation pattern analysis
- **Treasury Company Tracking**: Public company Bitcoin holdings monitoring
- **Predictive Analytics** ✨: 
  - Fee forecasting using exponential smoothing
  - Liquidity pressure analysis using z-score normalization
  - Confidence-based filtering (≥0.5 threshold)
  - Forward-looking insights with confidence intervals

## Architecture

The service is built with:
- **FastAPI**: High-performance async web framework
- **Pydantic**: Data validation and settings management
- **NumPy/SciPy**: Statistical analysis and signal processing
- **Google Cloud**: BigQuery and Pub/Sub integration (planned)

## API Endpoints

### Signal Processing
- `POST /process/signals` - Process block through signal generation pipeline
  - Runs all 6 processors in parallel (including predictive analytics)
  - Returns generated signals with timing metrics
  - Supports historical data for predictive models

### Block Ingestion
- `POST /ingest/block` - Ingest Bitcoin block into BigQuery
- `POST /cleanup` - Clean up data older than specified hours

### Status & Monitoring
- `GET /health` - Health check endpoint
- `GET /status` - Service status with processor information

## Project Structure

```
utxoiq-ingestion/
├── src/
│   ├── processors/
│   │   ├── base_processor.py         # Base processor interface
│   │   ├── mempool_processor.py      # Mempool signal processing
│   │   ├── exchange_processor.py     # Exchange flow detection
│   │   ├── miner_processor.py        # Miner treasury tracking
│   │   ├── whale_processor.py        # Whale accumulation detection
│   │   ├── treasury_processor.py     # Public company tracking
│   │   └── predictive_analytics.py   # Predictive models ✨
│   ├── pipeline_orchestrator.py      # Pipeline coordination
│   ├── signal_persistence.py         # BigQuery persistence
│   ├── monitoring.py                 # Cloud Monitoring integration
│   ├── error_handler.py              # Error handling & retry
│   ├── config.py                     # Configuration management
│   ├── models.py                     # Pydantic data models
│   └── main.py                       # FastAPI application
├── tests/
│   ├── mempool-processor.unit.test.py
│   ├── exchange-processor.unit.test.py
│   ├── predictive-analytics.unit.test.py
│   └── signal-persistence.integration.test.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your configuration
```

## Configuration

Required environment variables:

```bash
GCP_PROJECT_ID=your-project-id
BIGQUERY_DATASET_BTC=btc
BIGQUERY_DATASET_INTEL=intel
PUBSUB_TOPIC_SIGNALS=signal-generated
PUBSUB_SUBSCRIPTION_BLOCKS=block-processed
CONFIDENCE_THRESHOLD=0.7
MEMPOOL_SPIKE_THRESHOLD=3.0
REORG_DETECTION_DEPTH=6
```

## Running the Service

### Development Mode

```bash
# Run with auto-reload
python -m uvicorn src.main:app --reload --port 8080

# Or use the main module directly
python -m src.main
```

### Production Mode

```bash
# Run with uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 8080 --workers 4

# Or use Docker
docker build -t feature-engine .
docker run -p 8080:8080 --env-file .env feature-engine
```

## Testing

### Run All Tests

```bash
# Using pytest (if installed)
pytest tests/ -v

# Using the test runner script
python run_tests.py
```

### Test Coverage

The test suite covers:
- Fee quantile calculation algorithms
- Block inclusion time estimation
- Exchange flow anomaly detection
- Miner treasury delta computation
- Whale accumulation pattern analysis
- Predictive fee forecasting
- Liquidity pressure index calculation

## API Endpoints

### Health Check

```bash
GET /health
```

### Process Block

```bash
POST /process-block
Content-Type: application/json

{
  "block_data": {
    "block_hash": "...",
    "height": 800000,
    "timestamp": "2024-01-01T00:00:00Z",
    "size": 1000000,
    "tx_count": 2500,
    "fees_total": 2.5
  },
  "mempool_data": { ... },
  "exchange_flows": [ ... ],
  "miner_data": [ ... ],
  "whale_data": [ ... ]
}
```

### Individual Signal Endpoints

```bash
POST /compute-mempool-signal
POST /detect-exchange-flow
POST /analyze-miner-treasury
POST /track-whale-accumulation
POST /generate-predictive-signals
```

## Signal Types

### 1. Mempool Signals

Monitors mempool fee conditions and provides:
- Fee quantiles (p10, p25, p50, p75, p90)
- Block inclusion time estimates
- Fee spike detection
- Confidence scoring

### 2. Exchange Flow Signals

Detects unusual exchange activity:
- Entity-tagged transaction analysis
- Anomaly detection using z-scores
- Pattern recognition (volume spikes, large transactions)
- Evidence citations with transaction IDs

### 3. Miner Treasury Signals

Tracks mining entity balance changes:
- Daily balance change calculation
- Treasury delta with historical comparison
- Spending pattern analysis
- Entity attribution

### 4. Whale Accumulation Signals

Identifies whale accumulation patterns:
- Rolling 7-day accumulation analysis
- Whale wallet identification and classification
- Accumulation streak tracking
- Pattern detection (accelerating, consistent)

### 5. Predictive Signals

Forecasts future blockchain conditions:
- **Next Block Fee Forecast**: Temporal model predictions
- **Exchange Liquidity Pressure Index**: Flow pattern analysis
- Confidence intervals for predictions
- Model accuracy tracking

## Signal Confidence Scoring

All signals include a confidence score (0-1) based on:
- Data quality and completeness
- Historical pattern consistency
- Signal strength and magnitude
- Entity identification confidence

Signals with confidence ≥ 0.7 are automatically published.

## Development

### Adding New Signal Types

1. Create a new processor in `src/processors/`
2. Implement signal generation logic
3. Add to `SignalProcessor` in `signal_processor.py`
4. Create tests in `tests/`
5. Update API endpoints in `main.py`

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Document complex algorithms
- Write unit tests for new features

## Deployment

### Docker

```bash
# Build image
docker build -t utxoiq-feature-engine .

# Run container
docker run -p 8080:8080 --env-file .env utxoiq-feature-engine
```

### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy feature-engine \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## Performance

- Processes blocks within 60 seconds of detection
- Handles ~144 blocks per day (10-minute average)
- Supports concurrent signal processing
- Stateless design for horizontal scaling

## Monitoring

Key metrics to monitor:
- Signal generation latency
- Confidence score distribution
- Anomaly detection rate
- Prediction accuracy
- API response times

## Requirements

See `requirements.txt` for full dependency list. Key dependencies:
- fastapi >= 0.109.0
- numpy >= 1.24.0
- scipy >= 1.11.0
- pydantic >= 2.5.0

## License

Proprietary - utxoIQ Platform

## Support

For issues or questions, contact the utxoIQ development team.
