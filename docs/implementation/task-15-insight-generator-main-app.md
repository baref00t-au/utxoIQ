# Task 15: Insight Generator Service Main Application

**Status**: ✅ Complete  
**Date**: 2024-01-15  
**Requirements**: 3.1, 3.2, 3.5, 5.2

## Overview

Implemented a complete FastAPI application for the insight-generator service that wires together all insight generation components into a production-ready service with automatic background polling.

## Implementation Summary

### 1. FastAPI Application Structure (Subtask 15.1)

Created a FastAPI application with:

- **Lifespan Management**: Uses `@asynccontextmanager` to manage application lifecycle
- **Background Task**: Automatically starts polling loop on startup
- **Graceful Shutdown**: Properly cancels background tasks on shutdown
- **Health Checks**: `/health` endpoint for monitoring and diagnostics
- **Manual Triggers**: `/trigger-cycle` endpoint for testing
- **Statistics**: `/stats` endpoint for service metrics

**Key Features**:
- FastAPI 0.100+ lifespan pattern for background tasks
- Global service instance with lazy initialization
- Proper async/await patterns throughout
- Structured logging with correlation IDs

### 2. Polling Loop Implementation (Subtask 15.2)

Implemented `run_polling_loop()` background task that:

- Polls BigQuery for unprocessed signals every 10 seconds (configurable)
- Runs continuously until service shutdown
- Handles cancellation gracefully
- Retries on errors with configurable interval
- Logs all operations with correlation IDs

**Polling Cycle Flow**:
1. Poll for unprocessed signals (confidence >= 0.7)
2. Group signals by type and block height
3. Process each signal group
4. Generate insights using AI provider
5. Persist insights to BigQuery
6. Mark signals as processed
7. Wait for next cycle

### 3. Component Wiring (Subtask 15.3)

Created `InsightGeneratorService` class that initializes and wires together:

- **BigQuery Client**: For database operations
- **AI Provider**: Configured from environment (Vertex AI, OpenAI, Anthropic, Grok)
- **Signal Polling Module**: Polls and manages signal state
- **Insight Generation Module**: Generates insights from signals
- **Insight Persistence Module**: Persists insights to BigQuery

**Service Methods**:
- `process_signal_group()`: Processes a group of signals
- `run_polling_cycle()`: Executes one complete polling cycle

**Correlation ID Tracking**:
- Every polling cycle gets a unique UUID correlation ID
- All log messages include correlation ID
- Enables distributed tracing across services

## Files Created/Modified

### Created
- `services/insight-generator/src/main.py` - Complete rewrite with FastAPI structure
- `services/insight-generator/tests/test_main.unit.test.py` - Unit tests for main application
- `docs/implementation/task-15-insight-generator-main-app.md` - This document

### Modified
- `services/insight-generator/.env.example` - Added polling configuration
- `services/insight-generator/README.md` - Added FastAPI application documentation

## Configuration

### Environment Variables

```bash
# Google Cloud
GCP_PROJECT_ID=utxoiq-dev
DATASET_INTEL=intel

# Polling Configuration
POLL_INTERVAL_SECONDS=10
CONFIDENCE_THRESHOLD=0.7

# Service Configuration
PORT=8080
LOG_LEVEL=INFO

# AI Provider (choose one: vertex_ai, openai, anthropic, grok)
AI_PROVIDER=vertex_ai

# Provider-specific configuration
VERTEX_AI_PROJECT=utxoiq-dev
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-pro
```

## API Endpoints

### GET /
Service information and status.

### GET /health
Health check with diagnostics:
- Polling status
- AI provider name
- Unprocessed signal count
- Configuration details

### POST /trigger-cycle
Manually trigger a polling cycle (useful for testing).

### GET /stats
Service statistics:
- Unprocessed signals
- Stale signals (>1 hour old)
- Polling status

## Running the Service

### Development
```bash
cd services/insight-generator
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

### Production
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8080 --workers 1
```

### Docker
```bash
docker build -t insight-generator .
docker run -p 8080:8080 --env-file .env insight-generator
```

### Cloud Run
```bash
gcloud run deploy insight-generator \
  --source . \
  --region us-central1 \
  --platform managed \
  --set-env-vars GCP_PROJECT_ID=utxoiq-dev,AI_PROVIDER=vertex_ai
```

## Testing

### Unit Tests
```bash
cd services/insight-generator
pytest tests/test_main.unit.test.py -v
```

### Manual Testing
```bash
# Check health
curl http://localhost:8080/health

# Trigger cycle manually
curl -X POST http://localhost:8080/trigger-cycle

# Check stats
curl http://localhost:8080/stats
```

## How It Works

### Startup Sequence
1. FastAPI application starts
2. Lifespan context manager executes
3. `InsightGeneratorService` initialized
4. All modules initialized (polling, generation, persistence)
5. Background polling task started
6. Service ready to accept requests

### Polling Cycle
1. Generate correlation ID
2. Poll BigQuery for unprocessed signals
3. Group signals by type and block height
4. For each signal group:
   - For each signal:
     - Generate insight using AI provider
     - Persist insight to BigQuery
     - Mark signal as processed
5. Log cycle statistics
6. Wait for next cycle (10 seconds)

### Shutdown Sequence
1. Shutdown signal received
2. Set `is_running = False`
3. Cancel background polling task
4. Wait for task to complete
5. Clean shutdown

## Error Handling

- **AI Provider Errors**: Logged, signal remains unprocessed for retry
- **BigQuery Errors**: Logged, signal marked as unprocessed for retry
- **Polling Loop Errors**: Logged, wait and retry next cycle
- **Unexpected Errors**: Logged with full context, service continues

## Monitoring

### Logs
All operations logged with:
- Timestamp
- Log level
- Message
- Correlation ID (for polling cycles)
- Signal ID (for signal processing)
- Insight ID (for insight persistence)

### Metrics
- Unprocessed signal count
- Stale signal count (>1 hour old)
- Signals processed per cycle
- Insights generated per cycle
- Polling cycle duration

## Requirements Satisfied

✅ **3.1**: Poll for unprocessed signals with confidence >= 0.7  
✅ **3.2**: Group signals by type and block height  
✅ **3.5**: Mark signals as processed after successful insight creation  
✅ **5.2**: Wire together all components with correlation ID logging

## Next Steps

The insight-generator service is now complete and ready for deployment. Next tasks:

- **Task 16**: Implement Error Handler (optional)
- **Task 17**: Implement Monitoring Module (optional)
- **Task 18**: Implement Historical Backfill Module (optional)
- **Task 19**: Populate known entities database
- **Task 20**: Add environment variable configuration
- **Task 21**: Deploy services to Cloud Run
- **Task 22**: End-to-end pipeline testing

## Notes

- The service uses a single worker to avoid concurrent polling conflicts
- Polling interval is configurable via environment variable
- All modules are properly initialized with dependency injection
- Service can be tested locally without BigQuery using mocks
- Health check endpoint can be used for Kubernetes/Cloud Run health probes
