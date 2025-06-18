from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UserAssetCreate(BaseModel):
    """Schema for creating a new user asset"""
    asset_type: str
    file_path: str
    original_filename: str
    size: Optional[int] = None
    mime_type: Optional[str] = None
    description: Optional[str] = None

class UserAssetUpdate(BaseModel):
    """Schema for updating a user asset"""
    asset_type: Optional[str] = None
    file_path: Optional[str] = None
    original_filename: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    description: Optional[str] = None

class UserAssetResponse(BaseModel):
    """Schema for user asset response"""
    id: UUID
    user_id: UUID
    asset_type: str
    file_path: str
    original_filename: str
    size: Optional[int] = None
    mime_type: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True 