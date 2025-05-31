import uuid
from typing import Optional

from pydantic import BaseModel


class ProfileCreate(BaseModel):
    """Schema for creating a new profile"""
    full_name: Optional[str] = None


class ProfileUpdate(BaseModel):
    """Schema for updating an existing profile"""
    full_name: Optional[str] = None
    credits: Optional[int] = None
    stripe_customer_id: Optional[str] = None


class ProfileResponse(BaseModel):
    """Schema for profile response"""
    id: uuid.UUID
    full_name: Optional[str] = None
    credits: int
    stripe_customer_id: Optional[str] = None

    class Config:
        from_attributes = True 