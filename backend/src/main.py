"""
Main FastAPI application entry point - Development Mode.
Minimal configuration for frontend development testing.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager: runs on startup and shutdown.
    """
    # Startup
    logger.info("Backend initialized in development mode")
    yield
    # Shutdown
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="School ERP API - Development Mode",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "http://0.0.0.0:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health")
    async def health():
        return {"status": "healthy", "environment": settings.ENVIRONMENT}

    # Mock endpoints for frontend development
    @app.get("/api/health")
    async def api_health():
        return {"status": "ok", "message": "Backend API is running"}

    @app.get("/docs")
    async def swagger_ui():
        return JSONResponse({"message": "Swagger UI disabled in development mode"})

    return app


# Create FastAPI app instance
app = create_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager: runs on startup and shutdown.
    Creates database tables on startup (if database is available).
    """
    # Startup
    logger.info("Initializing database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialization complete")
    except Exception as e:
        logger.warning(f"Database connection failed (running in mock mode): {str(e)}")
        logger.info("Backend will run without database persistence")
    yield
    # Shutdown
    logger.info("Closing database engine...")
    try:
        await engine.dispose()
    except Exception:
        pass
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Enterprise Resource Planning system for Kenyan Secondary Schools",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS] or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security: Trusted Host Middleware (only in production)
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["example.com", "*.example.com"],  # Configure for your domain
        )

    # Response compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Health check endpoint
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": "1.0.0",
            "api_url": f"{settings.API_V1_STR}/docs",
        }

    # Register routers
    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(ledger_router, prefix=settings.API_V1_STR)
    app.include_router(fees_router, prefix=settings.API_V1_STR)
    app.include_router(reporting_router, prefix=settings.API_V1_STR)
    app.include_router(periods_router, prefix=settings.API_V1_STR)
    app.include_router(mpesa_router, prefix=settings.API_V1_STR)

    logger.info(f"FastAPI app created: {settings.PROJECT_NAME}")
    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
