from __future__ import annotations
from sqlalchemy import Column, Integer, Text, DateTime, func, ForeignKey, String, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
import secrets

from ..db import Base

# Generate a prefixed 8-hex-digit id like "u1a2b3c4" or "sdeadbeef"
def gen_hex_id(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(4)}"

class Users(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("id ~ '^U[0-9a-f]{8}$'", name="users_id_format_chk"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True, default=lambda: gen_hex_id("U"))
    displayname: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Foreign Keys (Integer)
    profile_id: Mapped[str | None] = mapped_column(Text, ForeignKey("user_profiles.id", ondelete="CASCADE"))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ORM relationships (one-to-one แบบ uselist=False)
    profile = relationship("UserProfiles", back_populates="user", uselist=False)
    job = relationship("Jobs", back_populates="user", uselist=True)

class UserProfiles(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint("id ~ '^UP[0-9a-f]{8}$'", name="user_profiles_id_format_chk"),
    )
    
    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True, default=lambda: gen_hex_id("UP"))
    first_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    gender: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("Users", back_populates="profile", uselist=False)