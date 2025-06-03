import uuid
from typing import Optional, Tuple

from app.models import Profile
from app.schemas import ProfileCreate, ProfileUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ProfileService:
    """Service class for Profile business logic using SQLAlchemy with Supabase PostgreSQL"""
    
    @staticmethod
    async def get_profile(db: AsyncSession, user_id: str) -> Optional[Profile]:
        """Get profile by user ID"""
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        result = await db.execute(select(Profile).filter(Profile.id == user_uuid))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_profile(db: AsyncSession, user_id: str, profile_data: ProfileCreate) -> Profile:
        """Create a new profile"""
        print("[ProfileService] Creating profile…")  # DEBUG
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        db_profile = Profile(
            id=user_uuid,
            full_name=profile_data.full_name,
            credits=1000,  # Default credits - updated to 1000 as requested
            stripe_customer_id=None
        )
        db.add(db_profile)
        try:
            # Commit once to persist to DB
            await db.commit()
            await db.refresh(db_profile)  # Refresh to get updated data
            print("[ProfileService] Profile committed and refreshed.")  # DEBUG
        except Exception as e:
            print(f"[ProfileService] Commit failed: {e}")
            raise
        return db_profile
    
    @staticmethod
    async def update_profile(db: AsyncSession, user_id: str, profile_data: ProfileUpdate) -> Optional[Profile]:
        """Update an existing profile"""
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        result = await db.execute(select(Profile).filter(Profile.id == user_uuid))
        db_profile = result.scalar_one_or_none()
        
        if not db_profile:
            return None
        
        # Update only provided fields
        if profile_data.full_name is not None:
            db_profile.full_name = profile_data.full_name
        if profile_data.credits is not None:
            db_profile.credits = profile_data.credits
        if profile_data.stripe_customer_id is not None:
            db_profile.stripe_customer_id = profile_data.stripe_customer_id
        
        await db.commit()  # Commit the transaction
        await db.refresh(db_profile)  # Refresh to get updated data
        return db_profile
    
    @staticmethod
    async def get_or_create_profile(db: AsyncSession, user_id: str, profile_data: Optional[ProfileCreate] = None) -> Tuple[Profile, bool]:
        """Get existing profile or create new one. Returns (profile, is_new)"""
        existing_profile = await ProfileService.get_profile(db, user_id)
        
        if existing_profile:
            return existing_profile, False
        
        # Create new profile
        create_data = profile_data or ProfileCreate()
        new_profile = await ProfileService.create_profile(db, user_id, create_data)
        return new_profile, True 