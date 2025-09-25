from __future__ import annotations
from sqlalchemy import Column, Integer, Text, DateTime, func, ForeignKey, Float, Boolean, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
import secrets

from ..db import Base

def gen_hex_id(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(4)}"

class Files(Base):
    __tablename__ = "files"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Size in bytes
    content_type: Mapped[str] = mapped_column(Text, nullable=False)  # MIME type
    file_hash: Mapped[str | None] = mapped_column(Text, nullable=True)  # For deduplication
    upload_by: Mapped[str | None] = mapped_column(Text, nullable=True)  # User ID who uploaded
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # ORM relationships
    user_profiles = relationship("UserProfiles", back_populates="profile_image", uselist=True)
    senior_profiles = relationship("SeniorProfiles", back_populates="profile_image", uselist=True)
    