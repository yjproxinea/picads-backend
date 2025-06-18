from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UserAdCreate(BaseModel):
    """Schema for creating a new user ad"""
    ad_type: str
    file_path: str
    name: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    tags: Optional[str] = None

class UserAdUpdate(BaseModel):
    """Schema for updating a user ad"""
    ad_type: Optional[str] = None
    file_path: Optional[str] = None
    name: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    tags: Optional[str] = None

class UserAdResponse(BaseModel):
    """Schema for user ad response"""
    id: UUID
    user_id: UUID
    ad_type: str
    file_path: str
    name: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True 