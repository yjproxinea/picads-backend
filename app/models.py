import uuid
from datetime import datetime

from app.database import Base
from sqlalchemy import ARRAY, DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)  # Supabase user ID (UUID)
    plan: Mapped[str] = mapped_column(Text, nullable=False, default='basic')
    stripe_customer_id: Mapped[str] = mapped_column(Text, nullable=True)
    payment_status: Mapped[str] = mapped_column(Text, nullable=True, default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class Credits(Base):
    """Credits model for tracking user credit balances"""
    __tablename__ = "credits"
    
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)
    included_credits: Mapped[int] = mapped_column(Integer, default=0)  # Credits included in subscription
    available_credits: Mapped[int] = mapped_column(Integer, default=0)  # Currently available credits (included + metered - used)
    metered_credits: Mapped[int] = mapped_column(Integer, default=0)  # Pay-as-you-go credits purchased via Stripe meter events
    total_used: Mapped[int] = mapped_column(Integer, default=0)  # Total credits used across all time
    last_refill: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class UsageLog(Base):
    __tablename__ = "usage_log"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)  # Foreign key to auth.users.id
    ad_type: Mapped[str] = mapped_column(Text, nullable=False)
    credits_used: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    extra_data: Mapped[dict] = mapped_column(JSONB, nullable=True)


class UserAssets(Base):
    __tablename__ = "user_assets"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)  # Foreign key to auth.users.id
    asset_type: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=True)
    size: Mapped[int] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
