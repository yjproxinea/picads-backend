import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Picads Backend...")
    logger.info(f"Environment: {getattr(settings, 'ENVIRONMENT', 'production')}")
    yield
    # Shutdown
    logger.info("Shutting down Picads Backend...")

app = FastAPI(
    title="Picads Backend",
    description="Backend API for Picads - AI-powered ad generation platform",
    version="1.0.0",
    docs_url="/docs" if getattr(settings, 'DEBUG', False) else None,
    redoc_url="/redoc" if getattr(settings, 'DEBUG', False) else None,
    lifespan=lifespan
)

# Production security middleware
if hasattr(settings, 'ALLOWED_HOSTS'):
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# CORS middleware - restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.4f}s"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Error: {request.method} {request.url} - "
            f"Exception: {str(e)} - "
            f"Time: {process_time:.4f}s"
        )
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy", 
        "service": "picads-backend",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Picads Backend API",
        "version": "1.0.0",
        "docs": "/docs" if getattr(settings, 'DEBUG', False) else "Documentation disabled in production"
    }

# Include API routes
app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_production:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Never use reload in production
        log_level="info"
    ) 