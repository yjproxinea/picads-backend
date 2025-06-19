import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_current_user
from app.database import get_db
from app.schemas import AdGenerationRequest
from app.services import AdGenerationService

router = APIRouter()

@router.post("/preview/text-ad")
async def preview_text_ad(
    request: AdGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate text ad preview without billing"""
    # Ensure ad_type is set correctly
    request.ad_type = "text_ad"
    
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    # Initialize ad generation service
    ad_service = AdGenerationService(db)
    
    # Generate ad preview
    response, error = await ad_service.generate_ad_preview(user_uuid, request)
    
    if error:
        raise HTTPException(status_code=400, detail=error.dict())
    
    return response

@router.post("/preview/image-ad")
async def preview_image_ad(
    request: AdGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate image ad preview without billing"""
    # Ensure ad_type is set correctly
    request.ad_type = "image_ad"
    
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    # Initialize ad generation service
    ad_service = AdGenerationService(db)
    
    # Generate ad preview
    response, error = await ad_service.generate_ad_preview(user_uuid, request)
    
    if error:
        raise HTTPException(status_code=400, detail=error.dict())
    
    return response

@router.post("/preview/video-ad")
async def preview_video_ad(
    request: AdGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate video ad preview without billing"""
    # Ensure ad_type is set correctly
    request.ad_type = "video_ad"
    
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    # Initialize ad generation service
    ad_service = AdGenerationService(db)
    
    # Generate ad preview
    response, error = await ad_service.generate_ad_preview(user_uuid, request)
    
    if error:
        raise HTTPException(status_code=400, detail=error.dict())
    
    return response

@router.post("/save/{ad_id}")
async def save_ad(
    ad_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save ad from draft to final (trigger billing and credit deduction)"""
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    # Initialize ad generation service
    ad_service = AdGenerationService(db)
    
    # Save ad
    response, error = await ad_service.save_ad(user_uuid, ad_id)
    
    if error:
        raise HTTPException(status_code=400, detail=error.dict())
    
    return response

# Keep existing endpoints for backward compatibility
@router.post("/generate/text-ad")
async def generate_text_ad(
    request: AdGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate text ad with credit billing and usage tracking"""
    # Ensure ad_type is set correctly
    request.ad_type = "text_ad"
    
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    # Initialize ad generation service
    ad_service = AdGenerationService(db)
    
    # Generate ad
    response, error = await ad_service.generate_ad(user_uuid, request)
    
    if error:
        raise HTTPException(status_code=400, detail=error.dict())
    
    return response

@router.post("/generate/image-ad")
async def generate_image_ad(
    request: AdGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate image ad with credit billing and usage tracking"""
    # Ensure ad_type is set correctly
    request.ad_type = "image_ad"
    
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    # Initialize ad generation service
    ad_service = AdGenerationService(db)
    
    # Generate ad
    response, error = await ad_service.generate_ad(user_uuid, request)
    
    if error:
        raise HTTPException(status_code=400, detail=error.dict())
    
    return response

@router.post("/generate/video-ad")
async def generate_video_ad(
    request: AdGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate video ad with credit billing and usage tracking"""
    # Ensure ad_type is set correctly
    request.ad_type = "video_ad"
    
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    # Initialize ad generation service
    ad_service = AdGenerationService(db)
    
    # Generate ad
    response, error = await ad_service.generate_ad(user_uuid, request)
    
    if error:
        raise HTTPException(status_code=400, detail=error.dict())
    
    return response 