import uuid
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Profile
from app.schemas import ProfileCreate, ProfileUpdate


class ProfileService:
    """Service class for Profile business logic using SQLAlchemy with Supabase PostgreSQL"""
    
    @staticmethod
    async def get_profile(db: AsyncSession, user_id: str) -> Optional[Profile]:
        """Get profile by user ID"""
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        result = await db.execute(select(Profile).filter(Profile.user_id == user_uuid))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_profile(db: AsyncSession, user_id: str, profile_data: ProfileCreate) -> Profile:
        """Create a new profile (credits are created separately via webhook after payment)"""
        print("[ProfileService] Creating profile...")  # DEBUG
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        
        # Create profile with pro plan
        db_profile = Profile(
            user_id=user_uuid,
            plan='pro',  # Set to pro since we only have one plan
            stripe_customer_id=profile_data.stripe_customer_id if hasattr(profile_data, 'stripe_customer_id') else None,
            payment_status='active',
            created_at=datetime.utcnow()
        )
        db.add(db_profile)
        
        try:
            # Commit profile only (credits handled by webhook after payment)
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
        result = await db.execute(select(Profile).filter(Profile.user_id == user_uuid))
        db_profile = result.scalar_one_or_none()
        
        if not db_profile:
            return None
        
        # Update only provided fields
        if hasattr(profile_data, 'plan') and profile_data.plan is not None:
            db_profile.plan = profile_data.plan
        if hasattr(profile_data, 'stripe_customer_id') and profile_data.stripe_customer_id is not None:
            db_profile.stripe_customer_id = profile_data.stripe_customer_id
        if hasattr(profile_data, 'payment_status') and profile_data.payment_status is not None:
            db_profile.payment_status = profile_data.payment_status
        
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