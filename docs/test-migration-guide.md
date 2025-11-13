# Test File Migration Guide

## Overview

This guide explains how to migrate test files to the new naming convention across all services.

## New Naming Convention

### Test File Names
- **Unit tests**: `*.unit.test.py` or `*.unit.test.ts`
- **Integration tests**: `*.integration.test.py` or `*.integration.test.ts`
- **E2E tests**: `*.e2e.test.py` or `*.e2e.test.ts`
- **Performance tests**: `*.performance.test.py` or `*.performance.test.ts`
- **Security tests**: `*.security.test.py` or `*.security.test.ts`

### Old vs New

| Old Pattern | New Pattern | Type |
|------------|-------------|------|
| `test_api.py` | `api.unit.test.py` | Unit test |
| `test_database.py` | `database.integration.test.py` | Integration test |
| `test_user_flow.py` | `user-flow.e2e.test.py` | E2E test |

## Migration Status

### ✅ All Services Migrated
- `utxoiq-ingestion` - 6 tests migrated
- `chart-renderer` - 4 tests migrated
- `data-ingestion` - 1 test migrated
- `email-service` - 6 tests migrated
- `insight-generator` - 5 tests migrated
- `web-api` - 39 tests migrated
- `x-bot` - 5 tests migrated
- Root `tests/e2e/` - 1 test migrated

**Total: 67 test files successfully migrated**

## Migration Steps

### 1. Identify Test Types

Review each test file and classify it:
- **Unit test**: Tests individual functions/classes in isolation
- **Integration test**: Tests interactions between components
- **E2E test**: Tests complete workflows

### 2. Rename Files

Use PowerShell (Windows) or bash (Unix) to rename files:

```powershell
# PowerShell example
Move-Item -Path "tests\test_api.py" -Destination "tests\api.unit.test.py"
Move-Item -Path "tests\test_database.py" -Destination "tests\database.integration.test.py"
```

```bash
# Bash example
mv tests/test_api.py tests/api.unit.test.py
mv tests/test_database.py tests/database.integration.test.py
```

### 3. Update pytest.ini

Update the service's `pytest.ini` to recognize new patterns:

```ini
[pytest]
testpaths = tests
python_files = *.test.py  # Changed from test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    security: Security tests
```

### 4. Update Imports

If tests import each other, update import statements:

```python
# Old
from tests.test_helpers import mock_data

# New
from tests.helpers import mock_data
```

### 5. Update CI/CD

Update any CI/CD scripts that reference test files:

```yaml
# Old
- pytest tests/test_*.py

# New
- pytest tests/*.test.py
```

### 6. Verify

Run the verification script:

```bash
python scripts/testing/verify-project-structure.py
```

## Example: Migrating web-api Service

```powershell
# Navigate to service
cd services/web-api/tests

# Rename unit tests
Move-Item test_api.py api.unit.test.py
Move-Item test_cache_service.py cache-service.unit.test.py
Move-Item test_database_service.py database-service.unit.test.py

# Rename integration tests
Move-Item test_api_database_integration.py api-database.integration.test.py
Move-Item test_stripe_integration.py stripe.integration.test.py

# Update pytest.ini
# (Edit services/web-api/pytest.ini as shown above)

# Run tests to verify
pytest
```

## Benefits

1. **Clear test categorization**: Immediately see test type from filename
2. **Better organization**: Easy to run specific test types
3. **Consistent across project**: Same pattern everywhere
4. **IDE support**: Better test discovery and filtering
5. **CI/CD optimization**: Run fast unit tests first, slow e2e tests later

## Best Practices

### Naming Guidelines
- Use kebab-case for multi-word names: `user-authentication.unit.test.py`
- Be descriptive: `stripe-payment-flow.integration.test.py` not `stripe.integration.test.py`
- Match source file names when testing specific modules

### Test Organization
- Keep helper files as `helpers.py`, `conftest.py`, `__init__.py`
- Group related tests in subdirectories if needed
- Add README.md to explain test structure

### Markers
Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_calculate_fee():
    """Unit test for fee calculation."""
    pass

@pytest.mark.integration
def test_database_connection():
    """Integration test for database."""
    pass
```

## Troubleshooting

### Tests not discovered
- Check `pytest.ini` has `python_files = *.test.py`
- Verify test functions start with `test_`
- Ensure `__init__.py` exists in test directories

### Import errors
- Update relative imports after renaming
- Check `conftest.py` is in correct location
- Verify PYTHONPATH includes service root

### CI/CD failures
- Update test file patterns in CI config
- Check coverage configuration
- Verify test discovery patterns

## Timeline

Migrate services incrementally:
1. Start with services with fewer tests
2. Migrate one service at a time
3. Update documentation as you go
4. Run full test suite after each migration

## Questions?

See [project-organization.md](project-organization.md) for overall structure guidelines.
