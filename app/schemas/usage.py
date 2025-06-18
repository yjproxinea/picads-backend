from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class UsageLogCreate(BaseModel):
    """Schema for creating a new usage log entry"""
    ad_type: str
    credits_used: int
    source: str
    extra_data: Optional[Dict[str, Any]] = None

class UsageLogResponse(BaseModel):
    """Schema for usage log response"""
    id: UUID
    user_id: UUID
    ad_type: str
    credits_used: int
    source: str
    created_at: datetime
    extra_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True 