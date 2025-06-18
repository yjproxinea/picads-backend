from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CreditsResponse(BaseModel):
    """Schema for credits response"""
    user_id: UUID
    included_credits: int
    metered_credits: int
    total_used: int
    last_refill: Optional[datetime] = None
    grace_until: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 