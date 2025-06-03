import os
from typing import List, Optional

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


settings = Settings() 