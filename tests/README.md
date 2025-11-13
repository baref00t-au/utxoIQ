# Test Structure

## Directory Organization

### Root Tests Directory
The root `tests/` directory contains **system-level tests** that span multiple services:

```
tests/
├── unit/              # Cross-service utility tests (if needed)
├── integration/       # Multi-service integration tests
├── e2e/              # End-to-end user workflow tests
├── performance/      # System-wide performance and load tests
└── security/         # Platform-wide security tests
```

### Service Tests
Each service maintains its own tests in `services/{service-name}/tests/`:

```
services/
├── web-api/tests/           # web-api service tests
├── utxoiq-ingestion/tests/  # ingestion service tests
├── insight-generator/tests/ # insight-generator service tests
└── ...
```

**Service tests** focus on:
- Unit tests for service-specific logic
- Integration tests for service dependencies (database, external APIs)
- Service-level functionality

**Root tests** focus on:
- Cross-service workflows
- Full user journeys
- System performance
- Platform security

## Naming Conventions

### Test Files
- **Unit tests**: `*.unit.test.py` or `*.unit.test.ts`
- **Integration tests**: `*.integration.test.py` or `*.integration.test.ts`
- **E2E tests**: `*.e2e.test.py` or `*.e2e.test.ts`
- **Performance tests**: `*.performance.test.py` or `*.performance.test.ts`
- **Security tests**: `*.security.test.py` or `*.security.test.ts`

### Examples
```
tests/
├── unit/
│   ├── processors.unit.test.py
│   ├── validators.unit.test.py
│   └── utils.unit.test.ts
├── integration/
│   ├── api-auth.integration.test.py
│   ├── database.integration.test.py
│   └── bigquery.integration.test.ts
├── e2e/
│   ├── block-to-insight-flow.e2e.test.py
│   ├── user-signup.e2e.test.ts
│   └── alert-creation.e2e.test.ts
├── performance/
│   ├── api-load.performance.test.py
│   └── query-optimization.performance.test.py
└── security/
    ├── auth-vulnerabilities.security.test.py
    └── sql-injection.security.test.py
```

## Running Tests

### Python Tests
```bash
# Run all tests
pytest

# Run specific test type
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/processors.unit.test.py
```

### TypeScript Tests
```bash
# Run all tests
npm test

# Run specific test type
npm test -- tests/unit
npm test -- tests/integration
npm test -- tests/e2e

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- tests/unit/utils.unit.test.ts
```

## Test Guidelines

### Unit Tests
- Test individual functions/classes in isolation
- Mock external dependencies
- Fast execution (< 1 second per test)
- 80%+ code coverage target
- Located in `tests/unit/`

### Integration Tests
- Test interactions between components
- Use test databases/services
- Moderate execution time (< 10 seconds per test)
- Test API endpoints, database operations
- Located in `tests/integration/`

### E2E Tests
- Test complete user workflows
- Use real or staging environments
- Slower execution (< 60 seconds per test)
- Test critical user paths
- Located in `tests/e2e/`

### Performance Tests
- Test system performance under load
- Measure response times, throughput
- Identify bottlenecks
- Located in `tests/performance/`

### Security Tests
- Test authentication/authorization
- Check for common vulnerabilities
- Validate input sanitization
- Located in `tests/security/`

## Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = *.test.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

### vitest.config.ts
```typescript
export default {
  test: {
    include: ['tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html']
    }
  }
}
```

## Best Practices

1. **Naming**: Use descriptive test names that explain what is being tested
2. **Isolation**: Each test should be independent and not rely on other tests
3. **Cleanup**: Always clean up test data and resources
4. **Mocking**: Mock external services in unit tests
5. **Assertions**: Use clear, specific assertions
6. **Documentation**: Add docstrings explaining complex test scenarios
7. **Speed**: Keep tests fast; move slow tests to integration/e2e
8. **Coverage**: Aim for 80%+ coverage on critical code paths
