# main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config.settings import OUTPUT_DIR, UPLOAD_DIR, VIDEO_DIR, VIDEO_IMAGE_DIR, WAVS_DIR, settings
from app.core.logging.logger import setup_logging, get_logger
# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("🚀 Application starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Version: {settings.APP_VERSION}")
    
    # Initialize any startup services here
    try:
        # Example: Initialize database connection pool
        # from app.db.database import init_db
        # await init_db()
        pass
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutting down...")
    
    # Cleanup any resources here
    try:
        # Example: Close database connections
        # from app.db.database import close_db
        # await close_db()
        pass
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """
    Application Factory
    - Production ready
    - Test friendly
    - Worker friendly
    """
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI Video REST API",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_DOCS else None,
        openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
    )
    
    # ---------------- CORS ----------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ---------------- Routers ----------------
    app.include_router(
        api_router,
        prefix=settings.API_PREFIX,
    )

    app.mount(
    "/api/wavs",
    StaticFiles(directory=str(WAVS_DIR)),
    name="wavs",
)


# Generated Viterbox audio
    app.mount(
        "/api/viterbox/outputs",
        StaticFiles(directory=str(OUTPUT_DIR)),
        name="viterbox-outputs",
    )


    # Uploaded Viterbox files
    app.mount(
        "/api/viterbox/uploads",
        StaticFiles(directory=str(UPLOAD_DIR)),
        name="viterbox-uploads",
    )

    app.mount(
        "/api/videos",
        StaticFiles(
            directory=str(VIDEO_DIR),
        ),
        name="generated-videos",
    )

    app.mount(
        "/api/video-images",
        StaticFiles(
            directory=str(VIDEO_IMAGE_DIR),
        ),
        name="video-images",
    )

    app.mount(
        "/api/ai-videos",
        StaticFiles(directory="outputs/ai-videos"),
        name="ai-videos",
    )

    
    # ---------------- Root Endpoint ----------------
    @app.get("/")
    async def root():
        return {
            "message": "AI Video Backend API",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "status": "running"
        }
    
    # ---------------- Health Check ----------------
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "version": settings.APP_VERSION
        }
    
    return app
# Create app instance
app = create_app()
