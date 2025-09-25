from __future__ import annotations
from sqlalchemy import Column, Integer, Text, DateTime, func, ForeignKey, Boolean, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
import secrets

from ..db import Base

# Generate a prefixed 8-hex-digit id
def gen_hex_id(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(4)}"

class ChatRooms(Base):
    __tablename__ = "chat_rooms"
    __table_args__ = (
        CheckConstraint("id ~ '^CR[0-9a-f]{8}$'", name="chat_rooms_id_format_chk"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True, default=lambda: gen_hex_id("CR"))
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    senior_id: Mapped[str] = mapped_column(Text, ForeignKey("senior_users.id", ondelete="CASCADE"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ORM relationships
    job = relationship("Jobs", back_populates="chat_room", uselist=False)
    user = relationship("Users", back_populates="chat_rooms", uselist=False)
    senior = relationship("SeniorUsers", back_populates="chat_rooms", uselist=False)
    messages = relationship("ChatMessages", back_populates="room", uselist=True, order_by="ChatMessages.created_at")

class ChatMessages(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("id ~ '^CM[0-9a-f]{8}$'", name="chat_messages_id_format_chk"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True, default=lambda: gen_hex_id("CM"))
    room_id: Mapped[str] = mapped_column(Text, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[str] = mapped_column(Text, nullable=False)  # Either user_id or senior_id
    sender_type: Mapped[str] = mapped_column(Text, nullable=False)  # "user" or "senior_user"
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ORM relationships
    room = relationship("ChatRooms", back_populates="messages", uselist=False)