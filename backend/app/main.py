"""
FastAPI application entry point.
"""

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_db, init_db


def setup_logging() -> None:
    """Configure structured JSON logging."""
    import loguru
    from loguru import logger
    
    logger.remove()
    
    if settings.LOG_FORMAT == "json":
        import json
        import datetime
        
        class JsonFormatter:
            def format(self, record):
                log_data = {
                    "timestamp": datetime.datetime.utcnow().isoformat(),
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

    return app


app = create_app()
