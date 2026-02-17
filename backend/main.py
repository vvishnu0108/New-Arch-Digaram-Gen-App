"""
FastAPI Backend for Architecture Diagram Agent

Main application entry point with CORS configuration and route registration.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from core.logging import get_logger, configure_uvicorn_logging
from routers import diagrams, documentation, validation
from utils import ensure_generated_dir

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    configure_uvicorn_logging()
    ensure_generated_dir()
    logger.info("Application started - Generated directory ready")
    yield
    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title="Architecture Diagram Agent API",
    description="AI-powered architecture diagram generation with Draw.IO integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for React frontend
# Get CORS origins from environment variable, fallback to localhost for development
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(diagrams.router)
app.include_router(documentation.router)
app.include_router(validation.router)

# Mount static files for generated diagrams
if os.path.exists("generated"):
    app.mount("/static", StaticFiles(directory="generated"), name="static")


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Architecture Diagram Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "diagrams": "/api/diagrams",
            "documentation": "/api/docs",
            "validation": "/api/validate"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=["generated/*", "*.pyc", "__pycache__"]
    )

