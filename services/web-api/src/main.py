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
    monitoring
)
from .models.errors import ErrorResponse, ErrorDetail, ErrorCode
from .middleware.response_headers import RateLimitHeadersMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting utxoIQ Web API")
    yield
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
