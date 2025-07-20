import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_current_user
from app.database import get_db
from app.schemas.social_media import (
    PlatformListResponse,
    SocialMediaApiKeyCreate,
    SocialMediaApiKeyListResponse,
    SocialMediaApiKeyResponse,
    SocialMediaApiKeySecureListResponse,
    SocialMediaApiKeySecureResponse,
    SocialMediaApiKeyUpdate,
)
from app.services.social_media import SocialMediaApiKeyService

router = APIRouter()


@router.post("", response_model=SocialMediaApiKeyResponse)
async def create_social_media_api_key(
    api_key_data: SocialMediaApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new social media API key"""
    try:
        api_key = await SocialMediaApiKeyService.create_api_key(
            db=db,
            user_id=uuid.UUID(current_user.id),
            api_key_data=api_key_data
        )
        return api_key
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create social media API key: {str(e)}"
        )


@router.get("", response_model=SocialMediaApiKeyListResponse)
async def get_user_social_media_api_keys(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    active_only: bool = Query(False, description="Show only active keys"),
    secure: bool = Query(True, description="Return secure (masked) response"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's social media API keys"""
    api_keys, total = await SocialMediaApiKeyService.get_user_api_keys(
        db=db,
        user_id=uuid.UUID(current_user.id),
        platform=platform,
        active_only=active_only,
        page=page,
        page_size=page_size
    )
    
    # Convert to secure response if requested
    if secure:
        secure_keys = [
            SocialMediaApiKeySecureResponse.model_validate(key) for key in api_keys
        ]
        return SocialMediaApiKeySecureListResponse(
            keys=secure_keys,
            total=total,
            page=page,
            page_size=page_size
        )
    else:
        regular_keys = [
            SocialMediaApiKeyResponse.model_validate(key) for key in api_keys
        ]
        return SocialMediaApiKeyListResponse(
            keys=regular_keys,
            total=total,
            page=page,
            page_size=page_size
        )


@router.get("/platforms", response_model=PlatformListResponse)
async def get_supported_platforms():
    """Get list of supported social media platforms"""
    platforms = SocialMediaApiKeyService.get_supported_platforms()
    return PlatformListResponse(platforms=platforms)


@router.get("/{api_key_id}", response_model=SocialMediaApiKeyResponse)
async def get_social_media_api_key(
    api_key_id: uuid.UUID,
    secure: bool = Query(True, description="Return secure (masked) response"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific social media API key by ID"""
    api_key = await SocialMediaApiKeyService.get_api_key_by_id(
        db=db,
        user_id=uuid.UUID(current_user.id),
        api_key_id=api_key_id
    )
    
    if not api_key:
        raise HTTPException(status_code=404, detail="Social media API key not found")
    
    if secure:
        return SocialMediaApiKeySecureResponse.model_validate(api_key)
    else:
        return SocialMediaApiKeyResponse.model_validate(api_key)


@router.get("/platform/{platform}", response_model=SocialMediaApiKeyResponse)
async def get_active_api_key_for_platform(
    platform: str,
    secure: bool = Query(True, description="Return secure (masked) response"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get active API key for a specific platform"""
    api_key = await SocialMediaApiKeyService.get_active_key_by_platform(
        db=db,
        user_id=uuid.UUID(current_user.id),
        platform=platform
    )
    
    if not api_key:
        raise HTTPException(
            status_code=404, 
            detail=f"No active API key found for platform: {platform}"
        )
    
    # Check if key is valid
    if not await SocialMediaApiKeyService.is_api_key_valid(api_key):
        raise HTTPException(
            status_code=410,
            detail=f"API key for platform {platform} is expired or inactive"
        )
    
    if secure:
        return SocialMediaApiKeySecureResponse.model_validate(api_key)
    else:
        return SocialMediaApiKeyResponse.model_validate(api_key)


@router.put("/{api_key_id}", response_model=SocialMediaApiKeyResponse)
async def update_social_media_api_key(
    api_key_id: uuid.UUID,
    api_key_data: SocialMediaApiKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update social media API key"""
    api_key = await SocialMediaApiKeyService.update_api_key(
        db=db,
        user_id=uuid.UUID(current_user.id),
        api_key_id=api_key_id,
        api_key_data=api_key_data
    )
    
    if not api_key:
        raise HTTPException(status_code=404, detail="Social media API key not found")
    
    return api_key


@router.patch("/{api_key_id}/deactivate")
async def deactivate_social_media_api_key(
    api_key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate (soft delete) social media API key"""
    success = await SocialMediaApiKeyService.deactivate_api_key(
        db=db,
        user_id=uuid.UUID(current_user.id),
        api_key_id=api_key_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Social media API key not found")
    
    return {"message": "Social media API key deactivated successfully"}


@router.delete("/{api_key_id}")
async def delete_social_media_api_key(
    api_key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Permanently delete social media API key"""
    success = await SocialMediaApiKeyService.delete_api_key(
        db=db,
        user_id=uuid.UUID(current_user.id),
        api_key_id=api_key_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Social media API key not found")
    
    return {"message": "Social media API key deleted successfully"} 