import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    model_config = {
        "extra": "ignore",
        "env_file": ".env"
    }
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    
    # Stripe Configuration
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")  # Optional for local dev
    STRIPE_PRICE_ID: str = os.getenv("STRIPE_PRICE_ID_SUBSCRIPTION", "")  # Single price ID for the subscription plan
    STRIPE_PRICE_ID_METERED: str = os.getenv("STRIPE_PRICE_ID_METERED", "")  # Single price ID for the credits plan
    STRIPE_METER_NAME: str = os.getenv("STRIPE_METER_NAME", "credit_as_you_go")  # Meter name for credit overage billing
    
    # Frontend URL for redirects
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Database Configuration Components
    USER: str = os.getenv("USER", "")
    PASSWORD: str = os.getenv("PASSWORD", "")
    HOST: str = os.getenv("HOST", "")
    PORT: str = os.getenv("PORT", "5432")
    DBNAME: str = os.getenv("DBNAME", "")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:8080",
        "http://localhost:5173",  # Vite dev server default
        "http://127.0.0.1:5173",  # Alternative localhost format
        "http://localhost:4173",  # Vite preview server
        "http://127.0.0.1:4173"   # Alternative localhost format
    ]
    
    @property
    def DATABASE_URL(self) -> Optional[str]:
        """Construct the SQLAlchemy connection string from components"""
        if all([self.USER, self.PASSWORD, self.HOST, self.DBNAME]):
            # Use asyncpg without SSL requirement
            return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DBNAME}"
        return None

# Ad Generation Pricing Configuration
AD_PRICING: Dict[str, int] = {
    "text_ad": 5,
    "image_ad": 10,
    "video_ad": 25,
}

# Stripe Configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID_BASIC = os.getenv("STRIPE_PRICE_ID_BASIC")
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