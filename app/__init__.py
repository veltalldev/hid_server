"""
Application factory - UPDATED VERSION
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import macros, scripts, actions, server
from app.api.v1 import utility_actions
from app.api.v1 import session

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="HID Server v4.0",
        description="Raspberry Pi HID Keyboard + Mouse Control Server",
        version="4.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers with API versioning
    app.include_router(server.router, tags=["server"])
    app.include_router(macros.router, prefix="/api/v1", tags=["macros"])
    app.include_router(scripts.router, prefix="/api/v1", tags=["scripts"])
    app.include_router(actions.router, prefix="/api/v1", tags=["actions"])
    app.include_router(utility_actions.router, prefix="/api/v1", tags=["utility-actions"])
    app.include_router(session.router, prefix="/api/v1", tags=["session"])
    
    # Backwards compatibility routes (no /api/v1 prefix)
    app.include_router(macros.router, tags=["macros-legacy"])
    app.include_router(scripts.router, tags=["scripts-legacy"])
    app.include_router(actions.router, tags=["actions-legacy"])
    app.include_router(utility_actions.router, tags=["utility-actions-legacy"])  # NEW
    app.include_router(session.router, tags=["session-legacy"])
    
    return app
