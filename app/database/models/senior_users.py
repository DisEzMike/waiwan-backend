from __future__ import annotations
from sqlalchemy import Column, Integer, Text, DateTime, func, ForeignKey, Boolean, String, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector
import secrets

from ..db import Base

# Generate a prefixed 8-hex-digit id like "s1a2b3c4"
def gen_hex_id(prefix: str) -> str:
    return f"{prefix.upper()}{secrets.token_hex(4)}"

class SeniorUsers(Base):
    __tablename__ = "senior_users"

    __table_args__ = (
        CheckConstraint("id ~ '^s[0-9a-f]{8}$'", name="senior_users_id_format_chk"),
    )

    id: Mapped[str] = mapped_column(String(9), primary_key=True, index=True, default=lambda: gen_hex_id("s"))
    displayname: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Foreign Keys (String(9))
    profile_id: Mapped[str | None] = mapped_column(String(9), ForeignKey("senior_profiles.id", ondelete="CASCADE"))
    ability_id: Mapped[str | None] = mapped_column(String(9), ForeignKey("senior_abilities.id", ondelete="CASCADE"))

    activated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ORM relationships (one-to-one แบบ uselist=False)
    profile = relationship("SeniorProfiles", back_populates="user", uselist=False)
    ability = relationship("SeniorAbilities", back_populates="user", uselist=False)

class SeniorProfiles(Base):
    __tablename__ = "senior_profiles"

    __table_args__ = (
        CheckConstraint("id ~ '^s[0-9a-f]{8}$'", name="senior_profiles_id_format_chk"),
    )

    id: Mapped[str] = mapped_column(String(9), primary_key=True, index=True, default=lambda: gen_hex_id("sp"))
    first_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    id_card: Mapped[str | None] = mapped_column(Text, nullable=True)
    addr_from_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    addr_current: Mapped[str | None] = mapped_column(Text, nullable=True)
    underlying_diseases: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_person: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    gender: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("SeniorUsers", back_populates="profile", uselist=False)

class SeniorAbilities(Base):
    __tablename__ = "senior_abilities"

    __table_args__ = (
        CheckConstraint("id ~ '^s[0-9a-f]{8}$'", name="senior_abilities_id_format_chk"),
    )

    id: Mapped[str] = mapped_column(String(9), primary_key=True, index=True, default=lambda: gen_hex_id("sa"))
    type: Mapped[str | None] = mapped_column(Text, nullable=True)
    career: Mapped[str | None] = mapped_column(Text, nullable=True)
    other_ability: Mapped[str | None] = mapped_column(Text, nullable=True)
    vehicle: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    offsite_work: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # file_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("senior_files.id", ondelete="CASCADE"), nullable=True)
    # embedding vector(384)
    embedding = Column(Vector(384), nullable=True)

    user = relationship("SeniorUsers", back_populates="ability", uselist=False)
    # file = relationship("SeniorFiles", back_populates="ability", uselist=False)
    
class SeniorFiles(Base):
    __tablename__ = "senior_files"

    __table_args__ = (
        CheckConstraint("id ~ '^s[0-9a-f]{8}$'", name="senior_files_id_format_chk"),
    )

    id: Mapped[str] = mapped_column(String(9), primary_key=True, index=True, default=lambda: gen_hex_id("sf"))
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ability = relationship("SeniorAbilities", back_populates="file", uselist=False)