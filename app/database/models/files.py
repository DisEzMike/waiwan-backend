from __future__ import annotations
from sqlalchemy import Column, Integer, Text, DateTime, func, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..db import Base

class Files(Base):
    __tablename__ = "files"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    filename: Mapped[str | None] = mapped_column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # ORM relationships
    user_profiles = relationship("UserProfiles", back_populates="profile_image", uselist=True)
    