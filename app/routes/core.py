from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_current_user, get_current_user_optional
from app.database import get_db
from app.services import CreditsService, ProfileService

router = APIRouter()

@router.get("/")
async def welcome():
    """Public welcome endpoint"""
    return {"message": "Welcome to Picads Backend!"}

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
    """Protected dashboard endpoint that returns basic user info, profile data, and credits"""
    profile = await ProfileService.get_profile(db, current_user.id)
    credits = await CreditsService.get_credits(db, current_user.id)

    response: Dict[str, Any] = {
        "message": "Welcome to your dashboard!",
        "user_id": current_user.id,
        "email": current_user.email,
    }

    if profile:
        response["profile"] = {
            "plan": profile.plan,
            "payment_status": profile.payment_status,
            "stripe_customer_id": profile.stripe_customer_id,
        }
    
    if credits:
        response["credits"] = {
            "included_credits": credits.included_credits,
            "metered_credits": credits.metered_credits,
            "total_used": credits.total_used,
            "available": credits.available_credits if credits else 0
        }

    return response 