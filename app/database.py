import uuid
from typing import Optional

from app.config import settings
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool  # Add NullPool for no pooling

# Create Base class
Base = declarative_base()

# Initialize engine and session as None
engine = None
AsyncSessionLocal = None


# Create database engine using Supabase PostgreSQL
if settings.DATABASE_URL:
    # Create async database engine with PgBouncer-transaction compatibility
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
elif settings.SUPABASE_URL:
    # If no DATABASE_URL but we have Supabase, construct the connection string
    # Note: You'll need to get the actual database connection string from Supabase
    print("Warning: Using Supabase requires DATABASE_URL. Please get your PostgreSQL connection string from Supabase project settings.")

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