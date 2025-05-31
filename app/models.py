import uuid

from app.database import Base
from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)  # Supabase user ID (UUID)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    credits: Mapped[int] = mapped_column(default=100)
    stripe_customer_id: Mapped[str] = mapped_column(String, nullable=True)
