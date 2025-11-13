# chart-renderer Tests

## Test Files

- `api.unit.test.py` - API endpoint tests
- `models.unit.test.py` - Data model tests
- `renderers.unit.test.py` - Chart rendering logic tests
- `storage.integration.test.py` - Cloud Storage integration tests

## Running Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/api.unit.test.py

# Run with coverage
pytest --cov=src tests/
```
