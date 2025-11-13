# email-service Tests

## Test Files

- `api.unit.test.py` - API endpoint tests
- `email-service.unit.test.py` - Email service logic tests
- `email-templates.unit.test.py` - Email template rendering tests
- `engagement-tracking.unit.test.py` - Email engagement tracking tests
- `preference-management.unit.test.py` - User preference management tests
- `unsubscribe-flow.integration.test.py` - Unsubscribe workflow integration tests

## Running Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/email-service.unit.test.py

# Run with coverage
pytest --cov=src tests/
```
