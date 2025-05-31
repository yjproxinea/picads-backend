from typing import Any, Dict, Optional

from app.auth import User, get_current_user, get_current_user_optional
from app.database import get_db
from app.schemas import ProfileCreate, ProfileResponse, ProfileUpdate
from app.services import ProfileService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/")
async def welcome():
    """Public welcome endpoint"""
    return {"message": "Welcome to Picads Backend!"}

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's profile"""
    profile = await ProfileService.get_profile(db, current_user.id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return ProfileResponse.model_validate(profile)

@router.post("/profile", response_model=ProfileResponse)
async def create_or_get_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or get user profile"""
    profile, is_new = await ProfileService.get_or_create_profile(
        db, current_user.id, profile_data
    )
    
    return ProfileResponse.model_validate(profile)

@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    profile = await ProfileService.update_profile(db, current_user.id, profile_data)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return ProfileResponse.model_validate(profile)

@router.get("/public-data")
async def get_public_data(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Optional auth route - works with or without token"""
    if current_user:
        return {
            "message": "Personalized data for authenticated user",
            "user_email": current_user.email,
            "data": "Premium content here..."
        }
    else:
        return {
            "message": "Public data for anonymous user",
            "data": "Basic content here..."
        }

@router.get("/dashboard")
async def dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Protected dashboard endpoint that returns basic user info and profile data"""
    profile = await ProfileService.get_profile(db, current_user.id)

    response: Dict[str, Any] = {
        "message": "Welcome to your dashboard!",
        "user_id": current_user.id,
        "email": current_user.email,
    }

    if profile:
        response["profile"] = {
            "full_name": profile.full_name,
            "credits": profile.credits,
            "stripe_customer_id": profile.stripe_customer_id,
        }

    return response 