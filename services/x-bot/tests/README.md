# x-bot Tests

## Test Files

- `api.unit.test.py` - API endpoint tests
- `daily-brief-service.unit.test.py` - Daily brief generation tests
- `posting-service.unit.test.py` - X (Twitter) posting service tests
- `rate-limiting.unit.test.py` - Rate limiting logic tests
- `thread-generation.unit.test.py` - Thread generation tests

## Running Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/posting-service.unit.test.py

# Run with coverage
pytest --cov=src tests/
```
