from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import router

app = FastAPI(
    title="Picads Backend",
    description="Backend API for Picads - AI-powered ad generation platform",
    version="1.0.0"
)

# Add CORS middleware - TEMPORARY: Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

if __name__ == "__main__":
    import os

    import uvicorn
    uvicorn.run(
        "main:app",  # Correct import path for main.py in root directory
        host="0.0.0.0", 
        port=int(os.getenv("PORT", 8000)),  # Use $PORT env var or default to 8000
        reload=True  # Enable auto-reload on code changes
    ) 