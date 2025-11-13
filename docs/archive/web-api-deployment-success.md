# Web API Deployment Success

## Deployment Details

**Date**: November 12, 2025  
**Service**: utxoiq-web-api-dev  
**Region**: us-central1  
**Project**: utxoiq-dev  
**Status**: ✅ Successfully Deployed

## Service URL

```
https://utxoiq-web-api-dev-544291059247.us-central1.run.app
```

## Issues Resolved

### 1. PostgreSQL Password Authentication Failure

**Problem**: Initial deployment failed with `asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"`

**Root Cause**: 
- Cloud SQL password was not set correctly
- Connection configuration was attempting to use Unix sockets with asyncpg (not supported)

**Solution**:
- Reset postgres user password using `gcloud sql users set-password`
- Added Cloud SQL Python Connector (`cloud-sql-python-connector[asyncpg]`) to requirements
- Updated `database.py` to use Cloud SQL Connector for async connections
- Connector handles authentication and connection management automatically

### 2. Middleware Initialization Error

**Problem**: `RuntimeError: Cannot add middleware after an application has started`

**Root Cause**: Tracing middleware was being added in the lifespan function, which runs after app startup

**Solution**: Moved tracing initialization to before app creation, before other middleware is added

## Configuration Changes

### 1. requirements.txt
Added Cloud SQL Python Connector:
```python
cloud-sql-python-connector[asyncpg]==1.7.0
```

### 2. database.py
Updated to use Cloud SQL Connector for Cloud Run deployments:
```python
from google.cloud.sql.connector import Connector

async def get_connection() -> asyncpg.Connection:
    """Get database connection using Cloud SQL Connector."""
    global connector
    if connector is None:
        connector = Connector()
    
    conn: asyncpg.Connection = await connector.connect_async(
        settings.cloud_sql_connection_name,
        "asyncpg",
        user=settings.db_user,
        password=settings.db_password,
        db=settings.db_name,
    )
    return conn
```

### 3. main.py
Moved tracing initialization before middleware setup:
```python
# Initialize distributed tracing (must be done before adding other middleware)
if settings.gcp_project_id:
    try:
        tracing_service = TracingService(...)
        tracing_service.instrument_fastapi(app)
        app.state.tracing_service = tracing_service
    except Exception as e:
        logger.warning(f"Failed to initialize tracing: {e}")
```

### 4. config.py
Simplified database URL construction:
```python
@property
def database_url(self) -> str:
    """Construct async database URL for SQLAlchemy."""
    # When Cloud SQL connection is configured, Cloud Run's proxy makes it available on 127.0.0.1
    # asyncpg uses TCP connections (doesn't support Unix sockets)
    return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
```

## Deployment Configuration

### Environment Variables
```bash
ENVIRONMENT=development
FIREBASE_PROJECT_ID=utxoiq
GCP_PROJECT_ID=utxoiq-dev
BIGQUERY_DATASET_INTEL=intel
BIGQUERY_DATASET_BTC=btc
VERTEX_AI_LOCATION=us-central1
CLOUD_SQL_CONNECTION_NAME=utxoiq-dev:us-central1:utxoiq-db-dev
DB_USER=postgres
DB_PASSWORD=utxoiq_SecurePass123!
DB_NAME=utxoiq
DB_HOST=127.0.0.1
DB_PORT=5432
STRIPE_SECRET_KEY=sk_test_dummy
STRIPE_WEBHOOK_SECRET=whsec_dummy
```

### Cloud Run Settings
- **Memory**: 1Gi
- **CPU**: 1
- **Min Instances**: 0
- **Max Instances**: 10
- **Timeout**: 300s
- **Cloud SQL Instance**: utxoiq-dev:us-central1:utxoiq-db-dev

## Verification

### Health Check
```bash
curl https://utxoiq-web-api-dev-544291059247.us-central1.run.app/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T11:35:15.540883",
  "version": "1.0.0"
}
```

### API Info
```bash
curl https://utxoiq-web-api-dev-544291059247.us-central1.run.app/
```

Response:
```json
{
  "name": "utxoIQ API",
  "version": "1.0.0",
  "description": "AI-powered Bitcoin blockchain intelligence platform",
  "docs": "/docs",
  "openapi": "/openapi.json"
}
```

### API Documentation
- **Swagger UI**: https://utxoiq-web-api-dev-544291059247.us-central1.run.app/docs
- **ReDoc**: https://utxoiq-web-api-dev-544291059247.us-central1.run.app/redoc
- **OpenAPI Spec**: https://utxoiq-web-api-dev-544291059247.us-central1.run.app/openapi.json

## Frontend Integration

The frontend `.env.local` has been updated with the new API URL:

```bash
NEXT_PUBLIC_API_URL=https://utxoiq-web-api-dev-544291059247.us-central1.run.app
NEXT_PUBLIC_WS_URL=wss://utxoiq-web-api-dev-544291059247.us-central1.run.app
```

## Next Steps

1. **Test API Endpoints**: Verify all endpoints are working correctly
2. **Database Schema**: Run Alembic migrations to create database tables
3. **Frontend Testing**: Test frontend integration with the deployed API
4. **Monitoring**: Set up Cloud Monitoring alerts for the service
5. **Security**: Review and update CORS settings for production
6. **Documentation**: Update API documentation with example requests/responses

## Deployment Command

To redeploy in the future:
```bash
.\scripts\deploy-web-api-with-db.bat
```

Or manually:
```bash
cd services\web-api
gcloud run deploy utxoiq-web-api-dev \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars="..." \
  --set-cloudsql-instances=utxoiq-dev:us-central1:utxoiq-db-dev \
  --project utxoiq-dev
```

## Cloud SQL Connection

The Cloud SQL Python Connector provides:
- Automatic IAM authentication support
- Connection pooling and management
- Automatic SSL/TLS encryption
- Support for both Unix sockets and TCP connections
- Compatibility with asyncpg for async operations

This is the recommended approach for connecting to Cloud SQL from Cloud Run services.
