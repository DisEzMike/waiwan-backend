from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..db import Base

class Jobs(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    status: Mapped[int | None] = mapped_column(Integer, ForeignKey("status.id", ondelete="CASCADE"), default=0, nullable=False)
    
    user_id: Mapped[str | None] = mapped_column(Text, ForeignKey("users.id", ondelete="CASCADE"))
    senior_id: Mapped[str | None] = mapped_column(Text, ForeignKey("senior_users.id", ondelete="CASCADE"))
    
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    work_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    vehicle: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),  nullable=False)

    # ORM relationships
    user = relationship("Users", back_populates="job", uselist=False)
    senior = relationship("SeniorUsers", back_populates="job", uselist=False)
    review =relationship("Reviews", back_populates="job", uselist=False)
    s = relationship("Status", back_populates="job", uselist=False)
    
class Status(Base):
    __tablename__ = "status"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=False)
    
    # ORM relationships
    job = relationship("Jobs", back_populates="s", uselist=True)