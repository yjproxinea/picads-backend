from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, validator


class SocialMediaApiKeyCreate(BaseModel):
    """Schema for creating a new social media API key"""
    platform: str
    api_key: str
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    valid_from: datetime
    valid_to: Optional[datetime] = None
    scopes: Optional[Dict[str, List[str]]] = None
    platform_user_id: Optional[str] = None
    platform_username: Optional[str] = None

    @validator('platform')
    def validate_platform(cls, v):
        allowed_platforms = [
            'facebook', 'instagram', 'tiktok', 'twitter', 'linkedin', 
            'youtube', 'snapchat', 'pinterest', 'reddit'
        ]
        if v.lower() not in allowed_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(allowed_platforms)}")
        return v.lower()

    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("API key cannot be empty")
        return v.strip()


class SocialMediaApiKeyUpdate(BaseModel):
    """Schema for updating an existing social media API key"""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_active: Optional[bool] = None
    scopes: Optional[Dict[str, List[str]]] = None
    platform_user_id: Optional[str] = None
    platform_username: Optional[str] = None

    @validator('api_key')
    def validate_api_key(cls, v):
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError("API key cannot be empty")
        return v.strip() if v else v


class SocialMediaApiKeyResponse(BaseModel):
    """Schema for social media API key response"""
    id: UUID
    user_id: UUID
    platform: str
    api_key: str  # In production, you might want to mask this for security
    api_secret: Optional[str] = None  # In production, you might want to mask this
    access_token: Optional[str] = None  # In production, you might want to mask this
    refresh_token: Optional[str] = None  # In production, you might want to mask this
    valid_from: datetime
    valid_to: Optional[datetime] = None
    is_active: bool
    scopes: Optional[Dict[str, List[str]]] = None
    platform_user_id: Optional[str] = None
    platform_username: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @validator('scopes', pre=True)
    def validate_scopes_field(cls, v):
        if isinstance(v, dict):
            return v
        return None


class SocialMediaApiKeyListResponse(BaseModel):
    """Schema for listing social media API keys"""
    keys: List[SocialMediaApiKeyResponse]
    total: int
    page: int
    page_size: int


class SocialMediaApiKeySecureResponse(SocialMediaApiKeyResponse):
    """Schema for secure response that masks sensitive fields"""
    api_key: str
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

    @validator('api_key', pre=True)
    def mask_api_key(cls, v):
        if v and len(v) > 8:
            return f"{v[:4]}{'*' * (len(v) - 8)}{v[-4:]}"
        return "****"

    @validator('api_secret', 'access_token', 'refresh_token', pre=True)
    def mask_sensitive_fields(cls, v):
        if v and len(v) > 8:
            return f"{v[:4]}{'*' * (len(v) - 8)}{v[-4:]}"
        elif v:
            return "****"
        return None


class SocialMediaApiKeySecureListResponse(BaseModel):
    """Schema for listing social media API keys with secure/masked fields"""
    keys: List[SocialMediaApiKeySecureResponse]
    total: int
    page: int
    page_size: int


class PlatformListResponse(BaseModel):
    """Schema for listing supported platforms"""
    platforms: List[str] 