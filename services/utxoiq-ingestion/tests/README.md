# utxoiq-ingestion Tests

## Test Structure

Tests for the utxoiq-ingestion service follow the project-wide naming conventions:

- **Unit tests**: `*.unit.test.py` - Test individual functions/classes
- **Integration tests**: `*.integration.test.py` - Test component interactions

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/data-extraction.unit.test.py

# Run with coverage
pytest --cov=src tests/

# Run with verbose output
pytest -v
```

## Test Files

- `data-extraction.unit.test.py` - Data extraction logic tests
- `entity-identification.unit.test.py` - Entity identification tests
- `exchange-processor.unit.test.py` - Exchange processor tests
- `mempool-processor.unit.test.py` - Mempool processor tests
- `predictive-analytics.unit.test.py` - Predictive analytics tests
- `signal-persistence.integration.test.py` - Signal persistence integration tests

## Configuration

See `pytest.ini` in the service root for pytest configuration.
