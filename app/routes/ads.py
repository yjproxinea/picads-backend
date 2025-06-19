import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_current_user
from app.database import get_db
from app.models import UserAds
from app.schemas import UserAdResponse

router = APIRouter()

@router.get("", response_model=List[UserAdResponse])
async def get_user_ads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ad_type: Optional[str] = None,
    is_draft: Optional[bool] = Query(None, description="Filter by draft status"),
    limit: int = 50,
    offset: int = 0
):
    """Get user's generated ads with optional filtering by type and draft status"""
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    query = select(UserAds).filter(UserAds.user_id == user_uuid)
    
    if ad_type:
        query = query.filter(UserAds.ad_type == ad_type)
    
    if is_draft is not None:
        query = query.filter(UserAds.is_draft == is_draft)
    
    result = await db.execute(
        query.order_by(UserAds.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    ads = result.scalars().all()
    
    return [UserAdResponse.model_validate(ad) for ad in ads]

@router.get("/drafts", response_model=List[UserAdResponse])
async def get_user_drafts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ad_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get user's draft ads"""
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    query = select(UserAds).filter(UserAds.user_id == user_uuid, UserAds.is_draft == True)
    
    if ad_type:
        query = query.filter(UserAds.ad_type == ad_type)
    
    result = await db.execute(
        query.order_by(UserAds.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    ads = result.scalars().all()
    
    return [UserAdResponse.model_validate(ad) for ad in ads]

@router.get("/saved", response_model=List[UserAdResponse])
async def get_user_saved_ads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ad_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get user's saved ads"""
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    query = select(UserAds).filter(UserAds.user_id == user_uuid, UserAds.is_draft == False)
    
    if ad_type:
        query = query.filter(UserAds.ad_type == ad_type)
    
    result = await db.execute(
        query.order_by(UserAds.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    ads = result.scalars().all()
    
    return [UserAdResponse.model_validate(ad) for ad in ads] 