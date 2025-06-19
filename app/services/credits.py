import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Credits


class CreditsService:
    """Service class for Credits business logic"""
    
    @staticmethod
    async def get_credits(db: AsyncSession, user_id: str) -> Optional[Credits]:
        """Get credits by user ID"""
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        result = await db.execute(select(Credits).filter(Credits.user_id == user_uuid))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_credits(db: AsyncSession, user_id: str, included_credits: int = 1000) -> Credits:
        """Create a new credits record for a user"""
        user_uuid = uuid.UUID(user_id)  # Convert string to UUID
        
        # Create credits record
        db_credits = Credits(
            user_id=user_uuid,
            included_credits=included_credits,
            available_credits=included_credits,  # Available credits start equal to included credits
            metered_credits=0,
            total_used=0,
            updated_at=datetime.utcnow()
        )
        db.add(db_credits)
        
        try:
            await db.commit()
            await db.refresh(db_credits)
            print(f"[CreditsService] Credits created for user {user_id} with {included_credits} credits")
        except Exception as e:
            print(f"[CreditsService] Commit failed: {e}")
            raise
        
        return db_credits


async def get_user_credits_summary(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
    """Get detailed credits summary for a user"""
    result = await db.execute(select(Credits).filter(Credits.user_id == user_id))
    credits = result.scalar_one_or_none()
    
    if not credits:
        return {
            "included_credits": 0,
            "metered_credits": 0,
            "total_used": 0,
            "available_credits": 0,
            "last_refill": None,
            "grace_until": None
        }
    
    return {
        "included_credits": credits.included_credits,
        "metered_credits": credits.metered_credits,
        "total_used": credits.total_used,
        "available_credits": credits.available_credits,
        "last_refill": credits.last_refill,
        "grace_until": credits.grace_until,
        "updated_at": credits.updated_at
    } 