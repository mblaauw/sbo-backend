"""
Main application entry point for SBO API.
This file combines all routes from different services.
"""

import logging
from fastapi import FastAPI, Depends

from config import get_settings
from database import init_db
from middleware import setup_middleware
from routes import (
    auth_routes, skills_routes, user_routes, 
    matching_routes, assessment_routes, llm_routes,
    dashboard_routes
)

logger = logging.getLogger("sbo.main")
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Skills Based Organization API",
    description="API for Skills Based Organization services",
    version=settings.app_version
)

# Set up middleware
setup_middleware(app)

# Include routers from all services
app.include_router(auth_routes.router)
app.include_router(skills_routes.router)
app.include_router(user_routes.router)
app.include_router(matching_routes.router)
app.include_router(assessment_routes.router)
app.include_router(llm_routes.router)
app.include_router(dashboard_routes.router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version
    }

# Initialize database and load mock data on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and load mock data on startup"""
    logger.info("Application starting up")
    
    # Initialize database schema
    init_db()
    
    # Import and initialize mock data
    from init_mock_data import init_mock_data_if_needed
    from database import get_db
    
    # Get a database session
    db = next(get_db())
    try:
        # Initialize mock data if needed
        init_mock_data_if_needed(db)
    finally:
        db.close()
    
    logger.info("Application startup complete")

if __name__ == "__main__":
    import uvicorn
    
    # Get host and port from settings
    host = settings.service.host
    port = settings.service.port
    
    # Run the application
    uvicorn.run("main:app", host=host, port=port, reload=settings.service.debug)