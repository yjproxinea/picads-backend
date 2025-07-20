import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserKeys
from app.schemas.social_media import SocialMediaApiKeyCreate, SocialMediaApiKeyUpdate


class SocialMediaApiKeyService:
    """Service class for handling social media API key operations"""
    
    @staticmethod
    async def create_api_key(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        api_key_data: SocialMediaApiKeyCreate
    ) -> UserKeys:
        """Create a new social media API key record"""
        # Check if user already has an active key for this platform
        existing_key = await SocialMediaApiKeyService.get_active_key_by_platform(
            db, user_id, api_key_data.platform
        )
        
        # If there's an existing active key, deactivate it
        if existing_key:
            existing_key.is_active = False
            await db.commit()
        
        db_api_key = UserKeys(
            user_id=user_id,
            platform=api_key_data.platform,
            api_key=api_key_data.api_key,
            api_secret=api_key_data.api_secret,
            access_token=api_key_data.access_token,
            refresh_token=api_key_data.refresh_token,
            valid_from=api_key_data.valid_from,
            valid_to=api_key_data.valid_to,
            scopes=api_key_data.scopes,
            platform_user_id=api_key_data.platform_user_id,
            platform_username=api_key_data.platform_username
        )
        
        db.add(db_api_key)
        await db.commit()
        await db.refresh(db_api_key)
        return db_api_key

    @staticmethod
    async def get_api_key_by_id(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        api_key_id: uuid.UUID
    ) -> Optional[UserKeys]:
        """Get API key by ID and user ID"""
        result = await db.execute(
            select(UserKeys).filter(
                and_(
                    UserKeys.id == api_key_id,
                    UserKeys.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_key_by_platform(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        platform: str
    ) -> Optional[UserKeys]:
        """Get active API key for a specific platform"""
        result = await db.execute(
            select(UserKeys).filter(
                and_(
                    UserKeys.user_id == user_id,
                    UserKeys.platform == platform.lower(),
                    UserKeys.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_api_keys(
        db: AsyncSession, 
        user_id: uuid.UUID,
        platform: Optional[str] = None,
        active_only: bool = False,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[UserKeys], int]:
        """Get user's API keys with optional filtering"""
        # Build base query
        query = select(UserKeys).filter(UserKeys.user_id == user_id)
        
        # Add filters
        if platform:
            query = query.filter(UserKeys.platform == platform.lower())
        if active_only:
            query = query.filter(UserKeys.is_active == True)
            
        # Add ordering
        query = query.order_by(UserKeys.created_at.desc())
        
        # Count total results
        count_result = await db.execute(query)
        total = len(count_result.fetchall())
        
        # Add pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        api_keys = result.scalars().all()
        
        return list(api_keys), total

    @staticmethod
    async def update_api_key(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        api_key_id: uuid.UUID,
        api_key_data: SocialMediaApiKeyUpdate
    ) -> Optional[UserKeys]:
        """Update API key"""
        result = await db.execute(
            select(UserKeys).filter(
                and_(
                    UserKeys.id == api_key_id,
                    UserKeys.user_id == user_id
                )
            )
        )
        db_api_key = result.scalar_one_or_none()
        
        if not db_api_key:
            return None
            
        # Update fields if provided in api_key_data
        update_data = api_key_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_api_key, field, value)
        
        # Update timestamp
        db_api_key.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(db_api_key)
        return db_api_key

    @staticmethod
    async def deactivate_api_key(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        api_key_id: uuid.UUID
    ) -> bool:
        """Deactivate (soft delete) API key"""
        result = await db.execute(
            select(UserKeys).filter(
                and_(
                    UserKeys.id == api_key_id,
                    UserKeys.user_id == user_id
                )
            )
        )
        db_api_key = result.scalar_one_or_none()
        
        if not db_api_key:
            return False
        
        db_api_key.is_active = False
        db_api_key.updated_at = datetime.utcnow()
        
        await db.commit()
        return True

    @staticmethod
    async def delete_api_key(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        api_key_id: uuid.UUID
    ) -> bool:
        """Permanently delete API key"""
        result = await db.execute(
            select(UserKeys).filter(
                and_(
                    UserKeys.id == api_key_id,
                    UserKeys.user_id == user_id
                )
            )
        )
        db_api_key = result.scalar_one_or_none()
        
        if not db_api_key:
            return False
        
        await db.delete(db_api_key)
        await db.commit()
        return True

    @staticmethod
    async def is_api_key_valid(api_key: UserKeys) -> bool:
        """Check if API key is currently valid"""
        now = datetime.utcnow()
        
        # Check if active
        if not api_key.is_active:
            return False
            
        # Check if valid_from has passed
        if api_key.valid_from > now:
            return False
            
        # Check if valid_to has not passed (None means no expiration)
        if api_key.valid_to and api_key.valid_to < now:
            return False
            
        return True

    @staticmethod
    def get_supported_platforms() -> List[str]:
        """Get list of supported social media platforms"""
        return [
            'facebook', 'instagram', 'tiktok', 'twitter', 'linkedin',
            'youtube', 'snapchat', 'pinterest', 'reddit'
        ] 