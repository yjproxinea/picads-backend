from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ProfileCreate(BaseModel):
    """Schema for creating a new profile"""
    stripe_customer_id: Optional[str] = None

class ProfileUpdate(BaseModel):
    """Schema for updating an existing profile"""
    plan: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    payment_status: Optional[str] = None

class ProfileResponse(BaseModel):
    """Schema for profile response"""
    user_id: UUID
    plan: str = "basic"
    stripe_customer_id: Optional[str] = None
    payment_status: str = "active"
    created_at: Optional[datetime] = None
    included_credits: int = 0
    metered_credits: int = 0
    total_used: int = 0
    available_credits: int = 0
    last_refill: Optional[datetime] = None
    grace_until: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 