from __future__ import annotations
from sqlalchemy import Column, Integer, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..db import Base

class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    displayname: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Foreign Keys (Integer)
    profile_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ORM relationships (one-to-one แบบ uselist=False)
    profile = relationship("UserProfiles", back_populates="user", uselist=False)
    job = relationship("Jobs", back_populates="job")

class UserProfiles(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    gender: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("Users", back_populates="profile", uselist=False)