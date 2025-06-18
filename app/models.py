import os
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, UUID, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

schema = os.getenv('DATABASE_SCHEMA', 'public')

class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {'schema': schema}

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)  # Primary key, no separate id
    plan: Mapped[str] = mapped_column(String, default="pro")
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    payment_status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Credits(Base):
    __tablename__ = "credits"
    __table_args__ = {'schema': schema}
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)  # Primary key, no separate id
    included_credits: Mapped[int] = mapped_column(Integer, default=1000)
    available_credits: Mapped[int] = mapped_column(Integer, default=1000) 
    metered_credits: Mapped[int] = mapped_column(Integer, default=0)
    total_used: Mapped[int] = mapped_column(Integer, default=0)
    last_refill: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class UsageLog(Base):
    __tablename__ = "usage_logs"
    __table_args__ = {'schema': schema}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ad_type: Mapped[str] = mapped_column(String, nullable=False)
    credits_used: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String, default="api_generation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSONB in Supabase


class UserAds(Base):
    __tablename__ = "user_ads"
    __table_args__ = {'schema': schema}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ad_type: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Text field, not array
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class UserAssets(Base):
    __tablename__ = "user_assets"
    __table_args__ = {'schema': schema}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    asset_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "logo", "image", "video", "document"
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class BrandIdentity(Base):
    __tablename__ = "brand_identities"
    __table_args__ = {'schema': schema}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    
    # Basic Info
    website_url: Mapped[str] = mapped_column(String, nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    value_proposition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Preferences
    ad_frequency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    team_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    monthly_budget: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Arrays stored as JSON
    brand_colors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    preferred_fonts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    platforms: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=datetime.utcnow)
