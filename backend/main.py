"""
main.py
-------
FastAPI application entry point for CarnaticGPT.
"""

import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers.upload_pdf import router as upload_router
from .routes import router as chat_router
from .services.faiss_store import FAISSStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "data/audio"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm up FAISS singleton (loads index from disk)
    logger.info("Initialising FAISSStore...")
    try:
        store = FAISSStore()
        stats = store.stats()
        logger.info(
            "FAISS ready: %d vectors | books: %d | by_type: %s",
            stats["total_vectors"], stats["indexed_books"], stats["by_type"],
        )
    except Exception as e:
        logger.warning("FAISSStore init skipped: %s", e)
    yield
    # Shutdown
    logger.info("Shutting down CarnaticGPT.")


app = FastAPI(
    title="CarnaticGPT API",
    version="2.0.0",
    description="Carnatic music knowledge assistant with production-grade FAISS pipeline",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve audio files as static
if AUDIO_DIR.exists():
    app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")

# Mount assets directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assets_dir = os.path.join(base_dir, 'assets')
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Routers
app.include_router(upload_router)
app.include_router(chat_router)


@app.get("/api/health")
async def health():
    try:
        store = FAISSStore()
        stats = store.stats()
        return {
            "status": "ok",
            "indexed_documents": stats["indexed_books"],
            "total_chunks": stats["total_chunks"],
            "by_type": stats["by_type"],
        }
    except Exception:
        return {
            "status": "ok",
            "indexed_documents": 0,
            "total_chunks": 0,
            "by_type": {},
        }


@app.get("/")
async def root():
    return {"message": "CarnaticGPT API v2.0 is running."}
