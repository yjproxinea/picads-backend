from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl, validator


class BrandIdentityCreate(BaseModel):
    """Schema for creating a new brand identity"""
    website_url: HttpUrl
    company_name: str
    value_proposition: Optional[str] = None
    industry: Optional[str] = None
    ad_frequency: Optional[str] = None
    team_size: Optional[int] = None
    monthly_budget: Optional[int] = None
    brand_colors: Optional[List[str]] = None
    preferred_fonts: Optional[List[str]] = None
    platforms: Optional[List[str]] = None

    @validator('ad_frequency')
    def validate_ad_frequency(cls, v):
        if v and v not in ['daily', 'weekly', 'biweekly', 'monthly']:
            raise ValueError('Invalid ad frequency')
        return v

    @validator('platforms')
    def validate_platforms(cls, v):
        valid_platforms = ['facebook', 'instagram', 'linkedin', 'twitter', 'tiktok', 'youtube', 'pinterest']
        if v:
            for platform in v:
                if platform not in valid_platforms:
                    raise ValueError(f'Invalid platform: {platform}')
        return v

class BrandIdentityUpdate(BaseModel):
    """Schema for updating an existing brand identity"""
    website_url: Optional[HttpUrl] = None
    company_name: Optional[str] = None
    value_proposition: Optional[str] = None
    industry: Optional[str] = None
    ad_frequency: Optional[str] = None
    team_size: Optional[int] = None
    monthly_budget: Optional[int] = None
    brand_colors: Optional[List[str]] = None
    preferred_fonts: Optional[List[str]] = None
    platforms: Optional[List[str]] = None

    _validate_ad_frequency = validator('ad_frequency', allow_reuse=True)(BrandIdentityCreate.validate_ad_frequency)
    _validate_platforms = validator('platforms', allow_reuse=True)(BrandIdentityCreate.validate_platforms)

class BrandIdentityResponse(BaseModel):
    """Schema for brand identity response"""
    id: UUID
    user_id: UUID
    website_url: str
    company_name: str
    value_proposition: Optional[str] = None
    industry: Optional[str] = None
    ad_frequency: Optional[str] = None
    team_size: Optional[int] = None
    monthly_budget: Optional[int] = None
    brand_colors: Optional[List[str]] = None
    preferred_fonts: Optional[List[str]] = None
    platforms: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 