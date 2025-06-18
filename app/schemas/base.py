from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class BillingInfo(BaseModel):
    """Schema for billing information"""
    credits_used: int
    metered_credits: Optional[int] = None

class AdGenerationRequest(BaseModel):
    """Schema for ad generation request"""
    ad_type: Literal["text_ad", "image_ad", "video_ad"]
    prompt: str
    target_audience: Optional[str] = None
    brand_guidelines: Optional[str] = None
    platform: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None

class AdGenerationResponse(BaseModel):
    """Schema for ad generation response"""
    success: bool
    message: str
    ad_type: str
    ad_id: Optional[UUID] = None
    ad_url: Optional[str] = None
    billing_info: BillingInfo
    usage_log_id: UUID
    generated_content: Optional[Dict[str, Any]] = None

class CreditTransaction(BaseModel):
    """Schema for credit transaction details"""
    transaction_type: Literal["deduction", "addition", "refund"]
    amount: int
    source: str
    description: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class PlanInfo(BaseModel):
    """Schema for plan information"""
    id: str
    name: str
    price: float
    currency: str
    period: str
    credits: int
    description: str
    features: List[str]

class InitSubscriptionRequest(BaseModel):
    """Schema for subscription initialization request"""
    plan: PlanInfo

class InitSubscriptionResponse(BaseModel):
    """Schema for subscription initialization response"""
    checkoutUrl: str
    customer_id: Optional[str] = None 