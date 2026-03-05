"""
Main FastAPI application entry point for Hotel Front Desk AI system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routes import router
from app.websocket_manager import WebSocketManager
from app.dependencies import get_websocket_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="Hotel Front Desk AI API",
        description="Conversational AI system for hotel front desk operations",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(router)
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on application startup."""
        logger.info("=" * 60)
        logger.info("Starting Hotel Front Desk AI API")
        logger.info("=" * 60)
        logger.info("Initializing WebSocket Manager...")
        ws_manager = get_websocket_manager()
        logger.info(f"WebSocket Manager initialized: {ws_manager}")
        logger.info("Application startup complete")
        logger.info(f"API available at: http://0.0.0.0:8000")
        logger.info(f"WebSocket endpoint: ws://0.0.0.0:8000/ws/chat")
        logger.info(f"REST endpoint: http://0.0.0.0:8000/api/chat")
        logger.info("=" * 60)
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on application shutdown."""
        logger.info("Shutting down Hotel Front Desk AI API...")
        logger.info("Application shutdown complete")
    
    return app


app = create_app()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "online", "service": "Hotel Front Desk AI API"}


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": "Hotel Front Desk AI API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
