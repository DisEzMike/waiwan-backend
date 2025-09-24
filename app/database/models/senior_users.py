from __future__ import annotations
from sqlalchemy import Column, Integer, Text, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from ..db import Base

class SeniorUsers(Base):
    __tablename__ = "senior_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    displayname: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Foreign Keys (Integer)
    profile_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("senior_profiles.id", ondelete="CASCADE"))
    ability_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("senior_abilities.id", ondelete="CASCADE"))

    activated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ORM relationships (one-to-one แบบ uselist=False)
    profile = relationship("SeniorProfiles", back_populates="user", uselist=False)
    ability = relationship("SeniorAbilities", back_populates="user", uselist=False)

class SeniorProfiles(Base):
    __tablename__ = "senior_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ability = relationship("SeniorAbilities", back_populates="file", uselist=False)