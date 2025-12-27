"""FastAPI backend for TGuard verification system."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import verification, static_files, health, external
from src.config.settings import config
from src.database.connection import init_database, close_database

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    logger.info("Starting TGuard API server...")

    # Initialize database
    await init_database()
    logger.info("Database initialized")

    yield

    # Cleanup
    logger.info("Shutting down TGuard API server...")
    await close_database()


# Create FastAPI app
app = FastAPI(
    title="TGuard API",
    description="Telegram Group Verification Bot API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include routers
app.include_router(verification.router, prefix="/api/v1")
app.include_router(external.router, prefix="/api")
app.include_router(static_files.router)
app.include_router(health.router)

# Mount static files for Mini Web App
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = asyncio.get_event_loop().time()

    response = await call_next(request)

    process_time = asyncio.get_event_loop().time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=False,
        log_level="info"
    )
