import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env.development")


class Settings(BaseSettings):
    model_config = {
        "extra": "ignore",
        "env_file": ".env"
    }
    
    # Environment Configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("ENVIRONMENT", "development") != "production"
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    
    # Stripe Configuration
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_ID_SUBSCRIPTION: str = os.getenv("STRIPE_PRICE_ID_SUBSCRIPTION", "")
    STRIPE_PRICE_ID_METERED: str = os.getenv("STRIPE_PRICE_ID_METERED", "")
    STRIPE_METER_NAME: str = os.getenv("STRIPE_METER_NAME", "credit_as_you_go")
    
    # Frontend URL for redirects
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Database Configuration Components
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "")
    
    # CORS - Environment-aware origins
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Get allowed origins based on environment"""
        if self.ENVIRONMENT == "production":
            # Production origins from environment variables
            origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
            return [origin.strip() for origin in origins if origin.strip()]
        else:
            # Development origins
            return [
                "http://localhost:3000", 
                "http://localhost:8080",
                "http://localhost:5173",  # Vite dev server default
                "http://127.0.0.1:5173",  # Alternative localhost format
                "http://localhost:4173",  # Vite preview server
                "http://127.0.0.1:4173"   # Alternative localhost format
            ]
    
    # Trusted hosts for production
    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        """Get allowed hosts for TrustedHostMiddleware"""
        if self.ENVIRONMENT == "production":
            hosts = os.getenv("ALLOWED_HOSTS", "").split(",")
            return [host.strip() for host in hosts if host.strip()]
        return ["*"]  # Allow all in development
    
    @property
    def DATABASE_URL(self) -> Optional[str]:
        """Get DATABASE_URL from environment or construct from components"""
        # First try to use the complete DATABASE_URL from environment
        complete_url = os.getenv('DATABASE_URL')
        if complete_url:
            return complete_url
            
        # Fallback to constructing from components
        if all([self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_NAME]):
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return None

# Ad Generation Pricing Configuration
AD_PRICING: Dict[str, int] = {
    "text_ad": 5,
    "image_ad": 10,
    "video_ad": 1005,
}

# Stripe Configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID_SUBSCRIPTION = os.getenv("STRIPE_PRICE_ID_SUBSCRIPTION")
STRIPE_PRICE_ID_METERED = os.getenv("STRIPE_PRICE_ID_METERED")  # For pay-as-you-go credits

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# File Upload Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "video": [".mp4", ".mov", ".avi", ".webm"],
    "text": [".txt", ".json", ".html"]
}

# Asset Storage Configuration
ASSETS_STORAGE_PATH = os.getenv("ASSETS_STORAGE_PATH", "./storage/assets")
ASSETS_BASE_URL = f"{API_BASE_URL}/assets"

settings = Settings() 