# Running Tests for Web API

This directory contains integration tests for the utxoIQ Web API service, including tests for authentication, authorization, subscription tiers, and rate limiting.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.12+ with dependencies installed (`pip install -r requirements.txt`)
- Alembic for database migrations

## Quick Start

### Windows (PowerShell)

```powershell
cd services/web-api
.\scripts\run-tests.ps1
```

### Windows (Command Prompt)

```cmd
cd services\web-api
scripts\run-tests.bat
```

### Linux/Mac

```bash
cd services/web-api
chmod +x scripts/run-tests.sh
./scripts/run-tests.sh
```

## What the Test Script Does

1. **Starts Docker containers** for PostgreSQL (port 5433) and Redis (port 6380)
2. **Waits for services** to become healthy
3. **Runs database migrations** using Alembic
4. **Executes tests** using pytest
5. **Cleans up** by stopping and removing containers

## Manual Testing

If you prefer to run tests manually:

### 1. Start Test Services

```bash
cd services/web-api
docker-compose -f docker-compose.test.yml up -d
```

### 2. Wait for Services

```bash
# Check status
docker-compose -f docker-compose.test.yml ps

# View logs if needed
docker-compose -f docker-compose.test.yml logs
```

### 3. Run Migrations

```bash
alembic upgrade head
```

### 4. Run Tests

```bash
# Run all endpoint protection tests
pytest tests/test_endpoint_protection_simple.py -v

# Run specific test class
pytest tests/test_endpoint_protection_simple.py::TestEndpointAuthenticationRequirements -v

# Run specific test
pytest tests/test_endpoint_protection_simple.py::TestEndpointAuthenticationRequirements::test_feedback_rate_requires_auth -v
```

### 5. Clean Up

```bash
docker-compose -f docker-compose.test.yml down
```

## Test Files

### Unit Tests
- `alert-configuration.unit.test.py` - Alert configuration tests
- `alert-evaluator-service.unit.test.py` - Alert evaluation logic tests
- `alert-history.unit.test.py` - Alert history tests
- `api.unit.test.py` - API endpoint tests
- `api-key-management.unit.test.py` - API key management tests
- `audit-logging.unit.test.py` - Audit logging tests
- `authentication-middleware.unit.test.py` - Authentication middleware tests
- `authorization.unit.test.py` - Authorization logic tests
- `backup-verification.unit.test.py` - Backup verification tests
- `cache-service.unit.test.py` - Cache service tests
- `dashboard-service.unit.test.py` - Dashboard service tests
- `database-service.unit.test.py` - Database service tests
- `db-models.unit.test.py` - Database model tests
- `db-model-structure.unit.test.py` - Database model structure tests
- `dependency-visualization-service.unit.test.py` - Dependency visualization tests
- `endpoint-protection-simple.unit.test.py` - Endpoint protection tests
- `error-tracking-service.unit.test.py` - Error tracking tests
- `guest-mode.unit.test.py` - Guest mode tests
- `log-aggregation-service.unit.test.py` - Log aggregation tests
- `metrics-service.unit.test.py` - Metrics service tests
- `notification-service.unit.test.py` - Notification service tests
- `openapi-schema.unit.test.py` - OpenAPI schema tests
- `profile-endpoints.unit.test.py` - Profile endpoint tests
- `profiling-service.unit.test.py` - Profiling service tests
- `protected-endpoints.unit.test.py` - Protected endpoint tests
- `rate-limiter.unit.test.py` - Rate limiter unit tests
- `retention-service.unit.test.py` - Data retention tests
- `tracing-service.unit.test.py` - Distributed tracing tests
- `user-models.unit.test.py` - User model tests

### Integration Tests
- `api-database.integration.test.py` - API-database integration tests
- `firebase-auth-service.integration.test.py` - Firebase authentication integration tests
- `rate-limiting.integration.test.py` - Rate limiting integration tests
- `stripe.integration.test.py` - Stripe payment integration tests
- `websocket.integration.test.py` - WebSocket integration tests

### Configuration
- `conftest.py` - Pytest configuration and fixtures

## Test Coverage

The tests verify:

### Authentication Requirements
- ✅ Feedback endpoints require authentication
- ✅ Alert endpoints require authentication
- ✅ Chat endpoints require authentication
- ✅ Monitoring endpoints require authentication

### Public Endpoints
- ✅ Health check is publicly accessible
- ✅ Root endpoint is publicly accessible
- ✅ Public insights endpoint works without auth
- ✅ Feedback stats are publicly accessible

### Rate Limiting
- ✅ Rate limit headers are present in responses
- ✅ Health check is not rate limited

### Error Handling
- ✅ Missing auth returns 401 with clear error message
- ✅ Invalid token format is rejected
- ✅ Nonexistent endpoints return 404
- ✅ Wrong HTTP methods return 405

### Security Headers
- ✅ Correlation ID is added to all responses
- ✅ CORS headers are configured

### Documentation
- ✅ OpenAPI schema is accessible
- ✅ Swagger docs are accessible
- ✅ ReDoc is accessible

## Troubleshooting

### Docker containers won't start

```bash
# Check if ports are already in use
netstat -an | findstr "5433"
netstat -an | findstr "6380"

# Stop any conflicting containers
docker ps
docker stop <container-id>
```

### Database migration fails

```bash
# Check database connection
docker-compose -f docker-compose.test.yml logs test-db

# Verify environment variables
cat .env.test

# Try running migration with verbose output
alembic upgrade head --sql
```

### Tests fail with connection errors

```bash
# Verify services are healthy
docker-compose -f docker-compose.test.yml ps

# Check service logs
docker-compose -f docker-compose.test.yml logs test-db
docker-compose -f docker-compose.test.yml logs test-redis

# Restart services
docker-compose -f docker-compose.test.yml restart
```

### Permission denied on scripts

```bash
# Linux/Mac: Make scripts executable
chmod +x scripts/run-tests.sh

# Windows: Run PowerShell as Administrator if needed
```

## CI/CD Integration

For GitHub Actions or other CI/CD pipelines:

```yaml
- name: Run tests
  run: |
    cd services/web-api
    docker-compose -f docker-compose.test.yml up -d
    sleep 10
    alembic upgrade head
    pytest tests/test_endpoint_protection_simple.py -v
    docker-compose -f docker-compose.test.yml down
```

## Environment Variables

Tests use `.env.test` configuration with:
- PostgreSQL on port 5433 (to avoid conflicts with dev database)
- Redis on port 6380 (to avoid conflicts with dev Redis)
- Mock Firebase credentials
- Test Stripe keys

## Notes

- Test database uses `tmpfs` for faster performance and automatic cleanup
- Each test run starts with a fresh database
- Tests are isolated and can run in parallel
- Mock services are used for external dependencies (Firebase, Stripe, etc.)
