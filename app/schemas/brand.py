from datetime import datetime
from typing import Dict, List, Optional
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
    brand_colors: Optional[Dict[str, List[str]]] = None
    preferred_fonts: Optional[Dict[str, List[str]]] = None
    platforms: Optional[Dict[str, List[str]]] = None

    @validator('brand_colors', 'preferred_fonts', 'platforms')
    def validate_nested_structure(cls, v):
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError("Must be a dictionary")
        if 'colors' not in v and 'fonts' not in v and 'platforms' not in v:
            raise ValueError("Must contain 'colors', 'fonts', or 'platforms' key")
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
    brand_colors: Optional[Dict[str, List[str]]] = None
    preferred_fonts: Optional[Dict[str, List[str]]] = None
    platforms: Optional[Dict[str, List[str]]] = None


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
    brand_colors: Optional[Dict[str, List[str]]] = None
    preferred_fonts: Optional[Dict[str, List[str]]] = None
    platforms: Optional[Dict[str, List[str]]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
    @validator('brand_colors', 'preferred_fonts', 'platforms', pre=True)
    def validate_array_fields(cls, v):
        if isinstance(v, dict):
            return v
        return None 