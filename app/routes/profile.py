from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_current_user
from app.database import get_db
from app.schemas import ProfileCreate, ProfileResponse, ProfileUpdate
from app.services import CreditsService, ProfileService

router = APIRouter()

@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's profile with credits"""
    profile = await ProfileService.get_profile(db, current_user.id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get credits for this user
    credits = await CreditsService.get_credits(db, current_user.id)
    
    # Create response with profile and credits data
    response_data = {
        "user_id": profile.user_id,
        "plan": profile.plan,
        "stripe_customer_id": profile.stripe_customer_id,
        "payment_status": profile.payment_status,
        "created_at": profile.created_at,
        # Include credits in the profile response
        "included_credits": credits.included_credits if credits else 0,
        "metered_credits": credits.metered_credits if credits else 0,
        "total_used": credits.total_used if credits else 0,
        "available_credits": credits.available_credits if credits else 0,
        # Include credits timestamps
        "last_refill": credits.last_refill if credits else None,
        "grace_until": credits.grace_until if credits else None,
        "updated_at": credits.updated_at if credits else None
    }
    
    return ProfileResponse.model_validate(response_data)

@router.post("", response_model=ProfileResponse)
async def create_profile_endpoint(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create user profile - only used after successful Stripe payment"""
    # Check if profile already exists
    existing_profile = await ProfileService.get_profile(db, current_user.id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    # Create new profile
    profile = await ProfileService.create_profile(db, current_user.id, profile_data)
    
    # Get credits for this user  
    credits = await CreditsService.get_credits(db, current_user.id)
    
    # Create response with profile and credits data
    response_data = {
        "user_id": profile.user_id,
        "plan": profile.plan,
        "stripe_customer_id": profile.stripe_customer_id,
        "payment_status": profile.payment_status,
        "created_at": profile.created_at,
        # Include credits in the profile response
        "included_credits": credits.included_credits if credits else 0,
        "metered_credits": credits.metered_credits if credits else 0,
        "total_used": credits.total_used if credits else 0,
        "available_credits": credits.available_credits if credits else 0,
        # Include credits timestamps
        "last_refill": credits.last_refill if credits else None,
        "grace_until": credits.grace_until if credits else None,
        "updated_at": credits.updated_at if credits else None
    }
    
    return ProfileResponse.model_validate(response_data)

@router.put("", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile with credits"""
    profile = await ProfileService.update_profile(db, current_user.id, profile_data)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get credits for this user
    credits = await CreditsService.get_credits(db, current_user.id)
    
    # Create response with profile and credits data
    response_data = {
        "user_id": profile.user_id,
        "plan": profile.plan,
        "stripe_customer_id": profile.stripe_customer_id,
        "payment_status": profile.payment_status,
        "created_at": profile.created_at,
        # Include credits in the profile response
        "included_credits": credits.included_credits if credits else 0,
        "metered_credits": credits.metered_credits if credits else 0,
        "total_used": credits.total_used if credits else 0,
        "available_credits": credits.available_credits if credits else 0,
        # Include credits timestamps
        "last_refill": credits.last_refill if credits else None,
        "grace_until": credits.grace_until if credits else None,
        "updated_at": credits.updated_at if credits else None
    }
    
    return ProfileResponse.model_validate(response_data) 