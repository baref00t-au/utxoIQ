# Scripts Directory

## Organization

```
scripts/
├── setup/           # Environment and service setup scripts
├── deployment/      # Deployment automation scripts
├── data/           # Data management and migration scripts
├── testing/        # Testing and verification scripts
└── bigquery/       # BigQuery-specific operations
```

## Setup Scripts (`setup/`)
Scripts for initial environment configuration and service setup.

- `local-dev.sh` - Local development environment setup
- `create-signal-tables.*` - Create signal processing tables
- `setup-retention-scheduler.*` - Configure data retention

## Deployment Scripts (`deployment/`)
Scripts for deploying services to cloud environments.

- `deploy-web-api.*` - Deploy web API service
- `deploy-utxoiq-ingestion.*` - Deploy ingestion service
- `deploy-feature-engine.*` - Deploy feature engine
- `deploy-block-monitor.*` - Deploy block monitor

## Data Scripts (`data/`)
Scripts for data management, backfill, and BigQuery operations.

- `backfill-*.py` - Historical data backfill scripts
- `analyze-blocks.py` - Block data analysis
- `create-bigquery-*.py` - BigQuery dataset creation
- `setup-bigquery*.py` - BigQuery configuration

## Testing Scripts (`testing/`)
Scripts for testing connections, services, and deployments.

- `test-bitcoin-connection.*` - Test Bitcoin Core connection
- `test-bigquery.py` - Test BigQuery connectivity
- `test-gemini-*.py` - Test Gemini AI integration
- `test-vertex-ai.py` - Test Vertex AI
- `verify-*.py` - Verification scripts

## BigQuery Scripts (`bigquery/`)
BigQuery-specific operations and maintenance.

- `cleanup-old-data.sh` - Data retention cleanup
- `create-hybrid-dataset.sh` - Hybrid dataset setup
- `create-unified-views.sh` - Create unified views
- `test-hybrid-queries.sh` - Test hybrid queries

## Usage

### Setup
```bash
# Local development
bash scripts/setup/local-dev.sh

# Create signal tables
bash scripts/setup/create-signal-tables.sh
```

### Deployment
```bash
# Deploy web API
bash scripts/deployment/deploy-web-api.sh

# Deploy ingestion service
scripts\deployment\deploy-utxoiq-ingestion.bat
```

### Data Management
```bash
# Backfill historical data
python scripts/data/backfill-blocks.py

# Setup BigQuery
python scripts/data/setup-bigquery.py
```

### Testing
```bash
# Test Bitcoin connection
python scripts/testing/test-bitcoin-connection.py

# Verify deployment
python scripts/testing/verify-deployment.py
```

## Naming Conventions

- **Shell scripts**: `kebab-case.sh` (Unix/Linux)
- **Batch scripts**: `kebab-case.bat` (Windows)
- **PowerShell scripts**: `kebab-case.ps1` (Windows)
- **Python scripts**: `kebab-case.py`

## Best Practices

1. **Idempotency**: Scripts should be safe to run multiple times
2. **Error Handling**: Include proper error checking and messages
3. **Documentation**: Add comments explaining complex operations
4. **Environment Variables**: Use `.env` files for configuration
5. **Logging**: Output clear progress and status messages
6. **Cleanup**: Clean up temporary files and resources
7. **Cross-platform**: Provide both `.sh` and `.bat` versions when possible
