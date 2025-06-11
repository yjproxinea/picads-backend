import uuid
from datetime import datetime
from typing import Any, Dict, Literal, Optional, Union

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
    user_id: uuid.UUID
    plan: str = "basic"
    stripe_customer_id: Optional[str] = None
    payment_status: str = "active"
    created_at: Optional[datetime] = None
    # Credits information included in profile response
    included_credits: int = 0
    metered_credits: int = 0
    total_used: int = 0
    available_credits: int = 0
    # Additional credits timestamps
    last_refill: Optional[datetime] = None
    grace_until: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreditsResponse(BaseModel):
    """Schema for credits response"""
    user_id: uuid.UUID
    included_credits: int
    metered_credits: int
    total_used: int
    last_refill: Optional[datetime] = None
    grace_until: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Usage Log Schemas
class UsageLogCreate(BaseModel):
    """Schema for creating a new usage log entry"""
    ad_type: str
    credits_used: int
    source: str
    extra_data: Optional[Dict[str, Any]] = None


class UsageLogResponse(BaseModel):
    """Schema for usage log response"""
    id: uuid.UUID
    user_id: uuid.UUID
    ad_type: str
    credits_used: int
    source: str
    created_at: datetime
    extra_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# User Ads Schemas (for generated ads)
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
    id: uuid.UUID
    user_id: uuid.UUID
    ad_type: str
    file_path: str
    name: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# User Assets Schemas (for user uploaded assets during onboarding)
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
    id: uuid.UUID
    user_id: uuid.UUID
    asset_type: str
    file_path: str
    original_filename: str
    size: Optional[int] = None
    mime_type: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Ad Generation Schemas
class AdGenerationRequest(BaseModel):
    """Schema for ad generation request"""
    ad_type: Literal["text_ad", "image_ad", "video_ad"]
    prompt: str
    target_audience: Optional[str] = None
    brand_guidelines: Optional[str] = None
    platform: Optional[str] = None  # e.g., "facebook", "instagram", "tiktok"
    additional_params: Optional[Dict[str, Any]] = None


class BillingInfo(BaseModel):
    """Schema for billing information"""
    credits_used: int
    metered_credits: Optional[int] = None  # Number of credits charged via Stripe metered billing


class AdGenerationResponse(BaseModel):
    """Schema for ad generation response"""
    success: bool
    message: str
    ad_type: str
    ad_id: Optional[uuid.UUID] = None
    ad_url: Optional[str] = None
    billing_info: BillingInfo
    usage_log_id: uuid.UUID
    generated_content: Optional[Dict[str, Any]] = None  # Placeholder for actual ad content


# Error Schemas
class ErrorResponse(BaseModel):
    """Schema for error responses"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# Credit Transaction Schemas
class CreditTransaction(BaseModel):
    """Schema for credit transaction details"""
    transaction_type: Literal["deduction", "addition", "refund"]
    amount: int
    source: str
    description: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


# New schemas for subscription handling
class PlanInfo(BaseModel):
    """Schema for plan information"""
    id: str
    name: str
    price: float
    currency: str
    period: str
    credits: int
    description: str
    features: list[str]


class InitSubscriptionRequest(BaseModel):
    """Schema for subscription initialization request"""
    plan: PlanInfo


class InitSubscriptionResponse(BaseModel):
    """Schema for subscription initialization response"""
    checkoutUrl: str
    customer_id: Optional[str] = None 