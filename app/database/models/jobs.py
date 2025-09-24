from __future__ import annotations
from sqlalchemy import Column, Integer, Text, DateTime, func, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..db import Base

class Jobs(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    status: Mapped[int | None] = mapped_column(Integer, ForeignKey("status.id", ondelete="CASCADE"), default=0, nullable=False)
    
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    senior_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("senior_users.id", ondelete="CASCADE"))
    
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    work_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    vehicle: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ORM relationships
    user = relationship("UserProfiles", back_populates="job", uselist=False)
    senior = relationship("SeniorProfiles", back_populates="job", uselist=False)
    s = relationship("Status", back_populates="job", uselist=False)
    
class Status(Base):
    __tablename__ = "status"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=False)