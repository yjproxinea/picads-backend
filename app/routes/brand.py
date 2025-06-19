import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_current_user
from app.database import get_db
from app.schemas import BrandIdentityCreate, BrandIdentityResponse, BrandIdentityUpdate
from app.services import BrandIdentityService

router = APIRouter()

@router.post("", response_model=BrandIdentityResponse)
async def create_brand_identity(
    brand_data: BrandIdentityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create brand identity for user"""
    try:
        brand = await BrandIdentityService.create_brand_identity(
            db=db,
            user_id=uuid.UUID(current_user.id),
            brand_data=brand_data
        )
        return brand
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create brand identity: {str(e)}"
        )

@router.get("", response_model=BrandIdentityResponse)
async def get_brand_identity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's brand identity"""
    brand = await BrandIdentityService.get_brand_identity(
        db=db, 
        user_id=uuid.UUID(current_user.id)
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand identity not found")
    return brand

@router.put("", response_model=BrandIdentityResponse)
async def update_brand_identity(
    brand_data: BrandIdentityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update brand identity"""
    brand = await BrandIdentityService.update_brand_identity(
        db=db,
        user_id=uuid.UUID(current_user.id),
        brand_data=brand_data
    )
    if not brand:
        raise HTTPException(status_code=404, detail="Brand identity not found")
    return brand 