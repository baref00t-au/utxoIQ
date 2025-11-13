"""Main FastAPI application for utxoIQ Web API."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from datetime import datetime
import uuid

from .config import settings
from .logging_config import configure_cloud_logging, set_correlation_id
from .services.tracing_service import TracingService
from .routes import (
    websocket,
    insights,
    alerts,
    feedback,
    daily_brief,
    chat,
    billing,
    email_preferences,
    white_label,
    monitoring,
    auth,
    filter_presets,
    export
)
from .models.errors import (
    ErrorResponse, ErrorDetail, ErrorCode,
    AuthenticationError, TokenExpiredError, InvalidTokenError,
    RevokedTokenError, InvalidAPIKeyError, InsufficientPermissionsError,
    RateLimitExceededError
)
from .middleware.response_headers import RateLimitHeadersMiddleware

# Configure Cloud Logging with structured output
configure_cloud_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting utxoIQ Web API")
    
    # Initialize database and monitoring
    from .database import init_db
    await init_db()
    
    yield
    
    # Cleanup
    from .database import close_db
    await close_db()
    logger.info("Shutting down utxoIQ Web API")


# Create FastAPI application
app = FastAPI(
    title="utxoIQ API",
    version="1.0.0",
    description="AI-powered Bitcoin blockchain intelligence platform",
    contact={
        "name": "utxoIQ Support",
        "url": "https://utxoiq.com/support",
        "email": "api@utxoiq.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://utxoiq.com/terms"
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Initialize distributed tracing (must be done before adding other middleware)
if settings.gcp_project_id:
    try:
        tracing_service = TracingService(
            project_id=settings.gcp_project_id,
            service_name="web-api"
        )
        tracing_service.instrument_fastapi(app)
        app.state.tracing_service = tracing_service
        logger.info("Distributed tracing initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize tracing: {e}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limit headers middleware
app.add_middleware(RateLimitHeadersMiddleware)


# Middleware to set correlation ID for request tracing
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to each request for tracing."""
    # Generate or extract correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Set in context for logging
    set_correlation_id(correlation_id)
    
    # Add trace context to current span if tracing is enabled
    if hasattr(app.state, 'tracing_service'):
        tracing_service = app.state.tracing_service
        tracing_service.add_span_attributes({
            "http.method": request.method,
            "http.url": str(request.url),
            "http.path": request.url.path,
            "http.user_agent": request.headers.get("user-agent", "unknown"),
            "correlation_id": correlation_id,
        })
        
        # Add client IP if available
        if request.client:
            tracing_service.add_span_attributes({
                "http.client_ip": request.client.host
            })
    
    # Process request
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    # Add trace ID to response headers if available
    if hasattr(app.state, 'tracing_service'):
        trace_id = app.state.tracing_service.get_current_trace_id()
        if trace_id:
            response.headers["X-Cloud-Trace-Context"] = trace_id
    
    # Add response status to span
    if hasattr(app.state, 'tracing_service'):
        app.state.tracing_service.add_span_attributes({
            "http.status_code": response.status_code
        })
    
    return response


# Custom OpenAPI schema with security schemes
def custom_openapi():
    """Generate custom OpenAPI schema with security schemes."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "FirebaseAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Firebase Auth JWT token"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for programmatic access"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Authentication exception handlers
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors with 401 responses."""
    request_id = str(uuid.uuid4())
    
    # Log authentication failure with details
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        f"Authentication failed [{request_id}]: {exc} | "
        f"IP: {client_ip} | Path: {request.url.path}"
    )
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.UNAUTHORIZED,
            message=str(exc),
            details={
                "path": request.url.path,
                "method": request.method
            }
        ),
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response.model_dump(),
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(TokenExpiredError)
async def token_expired_error_handler(request: Request, exc: TokenExpiredError):
    """Handle expired token errors."""
    request_id = str(uuid.uuid4())
    
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        f"Expired token [{request_id}]: {exc} | "
        f"IP: {client_ip} | Path: {request.url.path}"
    )
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token has expired",
            details={
                "path": request.url.path,
                "reason": "token_expired"
            }
        ),
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response.model_dump(),
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(InvalidTokenError)
async def invalid_token_error_handler(request: Request, exc: InvalidTokenError):
    """Handle invalid token errors."""
    request_id = str(uuid.uuid4())
    
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        f"Invalid token [{request_id}]: {exc} | "
        f"IP: {client_ip} | Path: {request.url.path}"
    )
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid authentication token",
            details={
                "path": request.url.path,
                "reason": "invalid_token"
            }
        ),
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response.model_dump(),
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(RevokedTokenError)
async def revoked_token_error_handler(request: Request, exc: RevokedTokenError):
    """Handle revoked token errors."""
    request_id = str(uuid.uuid4())
    
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        f"Revoked token [{request_id}]: {exc} | "
        f"IP: {client_ip} | Path: {request.url.path}"
    )
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token has been revoked",
            details={
                "path": request.url.path,
                "reason": "token_revoked"
            }
        ),
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response.model_dump(),
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(InvalidAPIKeyError)
async def invalid_api_key_error_handler(request: Request, exc: InvalidAPIKeyError):
    """Handle invalid API key errors."""
    request_id = str(uuid.uuid4())
    
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        f"Invalid API key [{request_id}]: {exc} | "
        f"IP: {client_ip} | Path: {request.url.path}"
    )
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid or revoked API key",
            details={
                "path": request.url.path,
                "reason": "invalid_api_key"
            }
        ),
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response.model_dump(),
        headers={"WWW-Authenticate": "ApiKey"}
    )


@app.exception_handler(InsufficientPermissionsError)
async def insufficient_permissions_error_handler(request: Request, exc: InsufficientPermissionsError):
    """Handle insufficient permissions errors with 403 responses."""
    request_id = str(uuid.uuid4())
    
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        f"Insufficient permissions [{request_id}]: {exc} | "
        f"IP: {client_ip} | Path: {request.url.path}"
    )
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.FORBIDDEN,
            message=str(exc),
            details={
                "path": request.url.path,
                "method": request.method
            }
        ),
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=error_response.model_dump()
    )


@app.exception_handler(RateLimitExceededError)
async def rate_limit_exceeded_error_handler(request: Request, exc: RateLimitExceededError):
    """Handle rate limit exceeded errors with 429 responses."""
    request_id = str(uuid.uuid4())
    
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        f"Rate limit exceeded [{request_id}]: {exc.message} | "
        f"IP: {client_ip} | Path: {request.url.path} | "
        f"Limit: {exc.limit} | Retry after: {exc.retry_after}s"
    )
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=exc.message,
            details={
                "path": request.url.path,
                "method": request.method,
                "limit": exc.limit,
                "remaining": exc.remaining,
                "retry_after": exc.retry_after,
                "window": "1h"
            }
        ),
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response.model_dump(),
        headers={
            "Retry-After": str(exc.retry_after),
            "X-RateLimit-Limit": str(exc.limit),
            "X-RateLimit-Remaining": str(exc.remaining),
            "X-RateLimit-Reset": str(exc.retry_after)
        }
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    request_id = str(uuid.uuid4())
    logger.error(f"Unhandled exception [{request_id}]: {exc}", exc_info=True)
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="An internal error occurred",
            details={"request_id": request_id}
        ),
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(websocket.router)
app.include_router(insights.router)
app.include_router(alerts.router)
app.include_router(feedback.router)
app.include_router(daily_brief.router)
app.include_router(chat.router)
app.include_router(billing.router)
app.include_router(email_preferences.router)
app.include_router(white_label.router)
app.include_router(monitoring.router)
app.include_router(filter_presets.router)
app.include_router(export.router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": app.title,
        "version": app.version,
        "description": app.description,
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )

