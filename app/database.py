import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool  # Add NullPool for no pooling

from app.config import settings

# Create Base class
Base = declarative_base()

# Initialize engine and session as None
engine = None
AsyncSessionLocal = None


# Create database engine using Supabase PostgreSQL
if settings.DATABASE_URL:
    # Create async database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        echo=False,  # Set to True for verbose SQL logging
    )
    
    # Create AsyncSessionLocal class
    AsyncSessionLocal = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False,
        autoflush=True,
        autocommit=False
    )
else:
    print("Warning: DATABASE_URL not configured. Please set DATABASE_URL environment variable.")

# Dependency to get async database session
async def get_db():
    if not AsyncSessionLocal:
        raise RuntimeError("Database not configured. Please set DATABASE_URL environment variable with your Supabase PostgreSQL connection string.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close() 