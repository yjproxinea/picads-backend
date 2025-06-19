import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserAssets
from app.schemas import UserAssetCreate


class AssetService:
    """Service class for handling user assets"""
    
    @staticmethod
    async def create_asset(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        asset_data: UserAssetCreate
    ) -> UserAssets:
        """Create a new user asset record"""
        db_asset = UserAssets(
            user_id=user_id,
            asset_type=asset_data.asset_type,
            file_path=asset_data.file_path,
            original_filename=asset_data.original_filename,
            size=asset_data.size,
            mime_type=asset_data.mime_type,
            description=asset_data.description
        )
        
        db.add(db_asset)
        await db.commit()
        await db.refresh(db_asset)
        return db_asset

    @staticmethod
    async def get_asset(db: AsyncSession, asset_id: uuid.UUID) -> Optional[UserAssets]:
        """Get asset by ID"""
        result = await db.execute(select(UserAssets).filter(UserAssets.id == asset_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_assets(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        asset_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[UserAssets]:
        """Get all assets for a user, optionally filtered by type"""
        query = select(UserAssets).filter(UserAssets.user_id == user_id)
        if asset_type:
            query = query.filter(UserAssets.asset_type == asset_type)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all()) 