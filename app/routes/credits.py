import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_current_user
from app.database import get_db
from app.models import UsageLog
from app.schemas import UsageLogResponse
from app.services import get_user_credits_summary

router = APIRouter()

@router.get("/summary")
async def get_credits_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed credits summary for current user"""
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    credits_summary = await get_user_credits_summary(db, user_uuid)
    return credits_summary

@router.get("/usage-log")
async def get_usage_log(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get user's usage log with pagination"""
    # Convert user ID to UUID
    user_uuid = uuid.UUID(current_user.id)
    
    result = await db.execute(
        select(UsageLog)
        .filter(UsageLog.user_id == user_uuid)
        .order_by(UsageLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    usage_logs = result.scalars().all()
    
    return [UsageLogResponse.model_validate(log) for log in usage_logs] 