# End-to-End System Tests

This directory contains end-to-end tests for the utxoIQ platform that verify complete data flows and system behavior.

## Test Coverage

### 1. Block-to-Insight Flow (`test_block_to_insight_flow.py`)

Tests the complete data pipeline from Bitcoin block detection to insight publication:

- **Block Processing**: Verifies blocks are ingested from Bitcoin node to BigQuery
- **Signal Generation**: Confirms signals are computed from block data
- **Insight Generation**: Validates AI-generated insights are created
- **WebSocket Notifications**: Tests real-time notifications to connected clients
- **Latency SLA**: Ensures block-to-insight latency < 60 seconds

**Requirements**: 7.1, 7.2

### 2. Blockchain Reorganization Handling

Tests system behavior during blockchain reorganizations:

- **Reorg Detection**: Verifies system detects chain reorganizations
- **Data Updates**: Confirms BigQuery data is updated with new chain
- **Insight Invalidation**: Validates old insights are marked invalid
- **New Insight Generation**: Ensures new insights are generated for reorganized blocks

**Requirements**: 7.5

### 3. Failover and Recovery

Tests system resilience and recovery:

- **Service Health Monitoring**: Verifies health check endpoints
- **Graceful Degradation**: Tests system behavior during service outages
- **Service Recovery**: Validates services restart and resume processing
- **Backlog Processing**: Confirms queued messages are processed after recovery

**Requirements**: 21.4

### 4. WebSocket Stability Under Load

Tests WebSocket connection stability:

- **Multiple Connections**: Creates 100 concurrent WebSocket connections
- **Message Broadcasting**: Verifies all connections receive broadcasts
- **Connection Success Rate**: Ensures > 95% connection success rate
- **Disconnection Rate**: Validates < 5% disconnection rate

**Requirements**: 7.1

### 5. Canary Deployment and Rollback

Tests deployment monitoring and rollback:

- **Canary Metrics**: Monitors error rate and latency for canary deployment
- **Threshold Checking**: Verifies rollback triggers when error rate > 1%
- **Traffic Routing**: Tests traffic split between canary and stable
- **Rollback Logic**: Validates automated rollback functionality

**Requirements**: 22.3

## Setup

### Prerequisites

1. **Bitcoin Node** (regtest mode for testing)
2. **GCP Project** with BigQuery and Pub/Sub enabled
3. **Running Services**:
   - web-api (port 8080)
   - feature-engine (port 8081)
   - insight-generator (port 8082)
   - chart-renderer (port 8083)

### Installation

```bash
# Install test dependencies
pip install -r requirements.txt

# Set up GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Configure Bitcoin node connection
export BITCOIN_RPC_HOST=localhost
export BITCOIN_RPC_PORT=8332
export BITCOIN_RPC_USER=bitcoin
export BITCOIN_RPC_PASSWORD=bitcoin
```

### Bitcoin Node Setup (Regtest)

```bash
# Start Bitcoin node in regtest mode
bitcoind -regtest -daemon \
  -rpcuser=bitcoin \
  -rpcpassword=bitcoin \
  -rpcport=8332 \
  -fallbackfee=0.00001

# Create wallet
bitcoin-cli -regtest createwallet "test"

# Generate initial blocks
bitcoin-cli -regtest generate 101
```

## Running Tests

### Run All E2E Tests

```bash
pytest tests/e2e/ -v
```

### Run Specific Test

```bash
pytest tests/e2e/test_block_to_insight_flow.py::TestBlockToInsightFlow::test_complete_block_processing_flow -v
```

### Run with Markers

```bash
# Run only fast tests
pytest tests/e2e/ -m "not slow"

# Run only tests requiring Bitcoin
pytest tests/e2e/ -m "requires_bitcoin"

# Run only tests requiring GCP
pytest tests/e2e/ -m "requires_gcp"
```

### Run with Coverage

```bash
pytest tests/e2e/ --cov=services --cov-report=html
```

### Run with Timeout

```bash
# Set custom timeout (default: 1800 seconds)
pytest tests/e2e/ --timeout=3600
```

## Test Configuration

### Environment Variables

```bash
# Bitcoin Node
BITCOIN_RPC_HOST=localhost
BITCOIN_RPC_PORT=8332
BITCOIN_RPC_USER=bitcoin
BITCOIN_RPC_PASSWORD=bitcoin

# GCP
GCP_PROJECT_ID=utxoiq-test
GCP_REGION=us-central1

# Services
WEB_API_URL=http://localhost:8080
FEATURE_ENGINE_URL=http://localhost:8081
INSIGHT_GENERATOR_URL=http://localhost:8082

# Test Configuration
TEST_TIMEOUT=1800
TEST_BLOCK_WAIT_TIMEOUT=900
```

### pytest.ini Configuration

The `pytest.ini` file configures:
- Test discovery patterns
- Test markers
- Asyncio mode
- Logging format
- Coverage settings
- Default options

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r tests/e2e/requirements.txt
      
      - name: Start Bitcoin node
        run: |
          docker run -d --name bitcoin \
            -p 8332:8332 \
            btcpayserver/bitcoin:24.0 \
            -regtest -rpcuser=bitcoin -rpcpassword=bitcoin
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Run E2E tests
        env:
          GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GCP_SA_KEY }}
          GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
        run: pytest tests/e2e/ -v --timeout=1800
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results/
```

## Troubleshooting

### Bitcoin Node Connection Issues

```bash
# Check Bitcoin node is running
bitcoin-cli -regtest getblockchaininfo

# Check RPC credentials
curl --user bitcoin:bitcoin \
  --data-binary '{"jsonrpc":"1.0","id":"test","method":"getblockcount","params":[]}' \
  http://localhost:8332
```

### Service Health Issues

```bash
# Check service health
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health

# Check service logs
docker-compose logs web-api
docker-compose logs feature-engine
docker-compose logs insight-generator
```

### BigQuery Connection Issues

```bash
# Verify GCP credentials
gcloud auth application-default print-access-token

# Test BigQuery access
bq query --use_legacy_sql=false "SELECT 1"

# Check dataset exists
bq ls utxoiq-test:
```

### WebSocket Connection Issues

```bash
# Test WebSocket connection
wscat -c ws://localhost:8080/ws

# Check WebSocket logs
docker-compose logs web-api | grep websocket
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Always clean up resources (connections, subscriptions) after tests
3. **Timeouts**: Set appropriate timeouts for long-running operations
4. **Retries**: Implement retries for flaky external dependencies
5. **Logging**: Use verbose logging to aid debugging
6. **Markers**: Use pytest markers to categorize tests
7. **Fixtures**: Use fixtures for common setup/teardown
8. **Assertions**: Use descriptive assertion messages

## Performance Benchmarks

Expected test durations:
- `test_complete_block_processing_flow`: 60-120 seconds
- `test_blockchain_reorganization_handling`: 30-60 seconds
- `test_failover_and_recovery`: 60-90 seconds
- `test_websocket_stability_under_load`: 30-45 seconds
- `test_canary_deployment_and_rollback`: 15-30 seconds

Total suite runtime: ~5-10 minutes

## Requirements Mapping

This test suite satisfies:
- **Requirement 7.1**: Block-to-insight latency < 60 seconds
- **Requirement 7.2**: Complete data flow validation
- **Requirement 7.5**: Blockchain reorganization handling
- **Requirement 21.4**: Failover and recovery testing
- **Requirement 22.3**: Canary deployment and rollback

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Bitcoin RPC API](https://developer.bitcoin.org/reference/rpc/)
- [Google Cloud BigQuery](https://cloud.google.com/bigquery/docs)
- [WebSocket Testing](https://websocket-client.readthedocs.io/)
