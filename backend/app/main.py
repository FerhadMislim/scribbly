"""
FastAPI application entry point.
"""

import sys
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_db, init_db
from app.routers import artwork

_logging_configured = False


def setup_logging() -> None:
    """Configure structured JSON logging."""
    global _logging_configured
    if _logging_configured:
        return

    from loguru import logger

    logger.remove()

    if settings.LOG_FORMAT == "json":
        import json

        class JsonFormatter:
            def format(self, record):
                log_data = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "level": record["level"].name,
                    "message": record["message"],
                    "module": record["module"],
                    "function": record["function"],
                    "line": record["line"],
                }
                if record["exception"]:
                    log_data["exception"] = str(record["exception"])
                return json.dumps(log_data)

        logger.add(
            sys.stdout,
            format="{message}",
            serialize=True,
            level=settings.LOG_LEVEL,
        )
    else:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.LOG_LEVEL,
        )

    _logging_configured = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    from loguru import logger

    logger.info("Starting application...")
    await init_db()
    yield
    logger.info("Shutting down application...")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    setup_logging()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": settings.APP_VERSION}

    app.include_router(artwork.router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
