# Test Organization Guide

## Where Do Tests Go?

### Service Tests → `services/{service-name}/tests/`

**Use for:**
- ✅ Unit tests for service functions/classes
- ✅ Integration tests for service dependencies (database, Redis, external APIs)
- ✅ Service-specific API endpoint tests
- ✅ Service business logic tests

**Examples:**
```
services/web-api/tests/
├── api.unit.test.py                    # API endpoint logic
├── database-service.unit.test.py       # Database service logic
├── stripe.integration.test.py          # Stripe API integration
└── firebase-auth-service.integration.test.py  # Firebase integration

services/utxoiq-ingestion/tests/
├── data-extraction.unit.test.py        # Data extraction logic
├── entity-identification.unit.test.py  # Entity identification
└── signal-persistence.integration.test.py  # BigQuery integration
```

### System Tests → `tests/`

**Use for:**
- ✅ End-to-end user workflows (signup → insight → alert)
- ✅ Multi-service integration tests
- ✅ System-wide performance/load tests
- ✅ Platform security tests

**Examples:**
```
tests/e2e/
└── block-to-insight-flow.e2e.test.py   # Block ingestion → insight generation

tests/integration/
└── api-to-bigquery.integration.test.py # web-api → BigQuery flow

tests/performance/
└── api-load.performance.test.py        # Load test across all APIs

tests/security/
└── auth-vulnerabilities.security.test.py  # Platform-wide auth testing
```

## Decision Tree

```
Is this test for a single service?
├─ YES → Put in services/{service-name}/tests/
│   │
│   ├─ Does it test internal logic?
│   │  └─ Use *.unit.test.py
│   │
│   └─ Does it test external dependencies?
│      └─ Use *.integration.test.py
│
└─ NO → Put in tests/
    │
    ├─ Does it test multiple services together?
    │  └─ Use tests/integration/*.integration.test.py
    │
    ├─ Does it test complete user workflows?
    │  └─ Use tests/e2e/*.e2e.test.py
    │
    ├─ Does it test system performance?
    │  └─ Use tests/performance/*.performance.test.py
    │
    └─ Does it test platform security?
       └─ Use tests/security/*.security.test.py
```

## Why This Structure?

### Service Tests (Colocated)
**Benefits:**
- Tests stay close to the code they test
- Service is self-contained and portable
- Can test service independently
- Clear ownership and responsibility
- Faster test discovery and execution

**When to use:**
- Testing service-specific functionality
- Mocking external dependencies
- Testing service in isolation

### System Tests (Root)
**Benefits:**
- Tests real integration between services
- Validates complete user journeys
- Tests system as a whole
- Catches integration issues

**When to use:**
- Testing cross-service workflows
- End-to-end user scenarios
- System-level concerns (performance, security)

## Examples by Scenario

### Scenario 1: Testing Alert Configuration Logic
**Location:** `services/web-api/tests/alert-configuration.unit.test.py`
**Why:** Service-specific business logic

### Scenario 2: Testing Stripe Payment Integration
**Location:** `services/web-api/tests/stripe.integration.test.py`
**Why:** Service integration with external API

### Scenario 3: Testing Block → Insight Flow
**Location:** `tests/e2e/block-to-insight-flow.e2e.test.py`
**Why:** Multi-service workflow (ingestion → feature-engine → insight-generator)

### Scenario 4: Testing API Load Handling
**Location:** `tests/performance/api-load.performance.test.py`
**Why:** System-wide performance testing

### Scenario 5: Testing Authentication Vulnerabilities
**Location:** `tests/security/auth-vulnerabilities.security.test.py`
**Why:** Platform-wide security concern

## Running Tests

### Run Service Tests
```bash
# Run all tests for a specific service
cd services/web-api
pytest

# Run specific test type
pytest tests/*.unit.test.py
pytest tests/*.integration.test.py
```

### Run System Tests
```bash
# Run all system tests
pytest tests/

# Run specific test type
pytest tests/e2e/
pytest tests/integration/
pytest tests/performance/
pytest tests/security/
```

### Run All Tests
```bash
# From project root
pytest services/*/tests/ tests/
```

## Best Practices

### Service Tests
1. Mock external dependencies (databases, APIs, other services)
2. Test in isolation - don't depend on other services running
3. Fast execution (< 1 second per unit test)
4. Focus on service-specific logic and behavior

### System Tests
1. Use real or staging environments
2. Test actual integration between services
3. Slower execution is acceptable (< 60 seconds per e2e test)
4. Focus on user journeys and system behavior

## Migration Notes

All services have been migrated to this structure:
- ✅ utxoiq-ingestion
- ✅ chart-renderer
- ✅ data-ingestion
- ✅ email-service
- ✅ insight-generator
- ✅ web-api
- ✅ x-bot

Total: 66 test files following new naming conventions.
