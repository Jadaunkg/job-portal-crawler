"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from .routes_jobs import router as jobs_router
from .routes_results import router as results_router
from .routes_admitcards import router as admit_cards_router
from .routes_system import router as system_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Job Portal Crawler API",
        description="RESTful API for accessing crawled job postings, exam results, and admit cards",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # ==================== CORS Configuration ====================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins (modify for production)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ==================== Register Routers ====================
    app.include_router(jobs_router, prefix="/api")
    app.include_router(results_router, prefix="/api")
    app.include_router(admit_cards_router, prefix="/api")
    app.include_router(system_router, prefix="/api")
    
    # ==================== Root Endpoint ====================
    @app.get(
        "/",
        summary="API Root",
        description="Welcome message and API information"
    )
    def root():
        """Root endpoint with API information."""
        return {
            "message": "Welcome to Job Portal Crawler API",
            "version": "1.0.0",
            "docs": "/api/docs",
            "redoc": "/api/redoc",
            "status": "/api/status",
            "stats": "/api/stats",
            "endpoints": {
                "jobs": "/api/jobs",
                "results": "/api/results",
                "admit_cards": "/api/admit-cards"
            }
        }
    
    # ==================== Health Check ====================
    @app.get("/health")
    def health_check():
        """Simple health check endpoint."""
        return {"status": "ok"}
    
    # ==================== Exception Handlers ====================
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Not Found", "detail": str(exc.detail)}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal Server Error", "detail": str(exc)}
        )
    
    # ==================== Custom OpenAPI Schema ====================
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Job Portal Crawler API",
            version="1.0.0",
            description="Complete REST API for job portal crawler system. Access jobs, results, and admit cards with advanced search and filtering.",
            routes=app.routes,
        )
        
        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
