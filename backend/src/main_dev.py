"""
Main FastAPI application - Development Mode.
Simplified backend for frontend development and testing.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logger.info("Backend server started")
    yield
    logger.info("Backend server shutdown")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="School ERP API",
        description="Development Backend for Frontend Testing",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS - Allow frontend on 5173
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://0.0.0.0:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/health")
    async def api_health():
        return {"status": "ok", "message": "API is running"}

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "School ERP Backend (Development Mode)",
            "frontend_url": "http://localhost:5173",
        }

    return app


# Create FastAPI app instance
app = create_app()
