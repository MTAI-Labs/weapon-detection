import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

from app.core.config import settings
from app.core.database import init_db, close_db, check_database_health
from app.api.routes import api_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up API", project=settings.PROJECT_NAME)
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Check database health
        db_healthy = await check_database_health()
        if not db_healthy:
            logger.error("Database health check failed during startup")
            raise Exception("Database connection failed")
        
        logger.info("API startup complete")
        
    except Exception as e:
        logger.error("Failed to start API", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down API")
    await close_db()
    logger.info("API shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=f"API for {settings.PROJECT_NAME} - PostgreSQL backend with auto-generated documentation",
    version=settings.VERSION,
    lifespan=lifespan,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
)

# CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Custom exception handlers (simplified from fullstack)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors"""
    logger.warning(
        "Validation error occurred",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation failed",
            "details": exc.errors(),
            "status_code": 422,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs_url": "/docs" if settings.DEBUG else None,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    db_healthy = await check_database_health()
    
    health_status = {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": f"{settings.PROJECT_NAME}-api",
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": "healthy" if db_healthy else "unhealthy",
        }
    }
    
    status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    if not db_healthy:
        logger.warning("Health check failed", checks=health_status["checks"])
    
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/info", tags=["info"], include_in_schema=settings.DEBUG)
async def get_info() -> Dict[str, Any]:
    """API information endpoint"""
    return {
        "name": f"{settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "database_pool_size": settings.DATABASE_POOL_SIZE,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG
    )