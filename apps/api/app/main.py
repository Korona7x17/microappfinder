from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.routers import runs, signals, clusters, briefs, exports, auth, reddit_search

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting MicroAppFinder API")
    # Initialize connections, etc.
    yield
    # Cleanup
    logger.info("Shutting down MicroAppFinder API")


app = FastAPI(
    title="MicroAppFinder API",
    description="API for discovering unmet demand for micro apps",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(reddit_search.router, prefix="/api/reddit", tags=["reddit"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(clusters.router, prefix="/api/clusters", tags=["clusters"])
app.include_router(briefs.router, prefix="/api/briefs", tags=["briefs"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])


@app.get("/")
async def root():
    return {"message": "MicroAppFinder API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
