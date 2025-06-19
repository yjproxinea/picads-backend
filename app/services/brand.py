import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BrandIdentity
from app.schemas import BrandIdentityCreate, BrandIdentityUpdate


class BrandIdentityService:
    """Service class for handling brand identity operations"""
    
    @staticmethod
    async def create_brand_identity(db: AsyncSession, user_id: uuid.UUID, brand_data: BrandIdentityCreate) -> BrandIdentity:
        """Create a new brand identity record"""
        db_brand = BrandIdentity(
            user_id=user_id,
            website_url=str(brand_data.website_url),
            company_name=brand_data.company_name,
            value_proposition=brand_data.value_proposition,
            industry=brand_data.industry,
            ad_frequency=brand_data.ad_frequency,
            team_size=brand_data.team_size,
            monthly_budget=brand_data.monthly_budget,
            brand_colors=brand_data.brand_colors,
            preferred_fonts=brand_data.preferred_fonts,
            platforms=brand_data.platforms
        )
        
        db.add(db_brand)
        await db.commit()
        await db.refresh(db_brand)
        return db_brand

    @staticmethod
    async def get_brand_identity(db: AsyncSession, user_id: uuid.UUID) -> Optional[BrandIdentity]:
        """Get brand identity by user ID"""
        result = await db.execute(select(BrandIdentity).filter(BrandIdentity.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_brand_identity(
        db: AsyncSession, 
        user_id: uuid.UUID, 
        brand_data: BrandIdentityUpdate
    ) -> Optional[BrandIdentity]:
        """Update brand identity"""
        result = await db.execute(select(BrandIdentity).filter(BrandIdentity.user_id == user_id))
        db_brand = result.scalar_one_or_none()
        
        if not db_brand:
            return None
            
        # Update fields if provided in brand_data
        update_data = brand_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'website_url' and value is not None:
                # Convert HttpUrl to string
                setattr(db_brand, field, str(value))
            elif field in ['brand_colors', 'preferred_fonts', 'platforms'] and value is not None:
                # Set JSON fields directly without double-wrapping
                setattr(db_brand, field, value)
            else:
                setattr(db_brand, field, value)
        
        await db.commit()
        await db.refresh(db_brand)
        return db_brand 