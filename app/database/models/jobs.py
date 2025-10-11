from __future__ import annotations
from sqlalchemy import Column, Integer, JSON, Table, Text, DateTime, func, ForeignKey, Float, Boolean, ARRAY, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chats import ChatRooms
    from .reviews import Reviews
    from .senior_users import SeniorUsers
    from .users import Users

from ..db import Base

class JobApplicationStatus(enum.Enum):
    PENDING = "pending"        # Senior was invited/applied but hasn't responded
    ACCEPTED = "accepted"      # Senior accepted the job
    DECLINED = "declined"      # Senior declined the job
    CANCELLED = "cancelled"    # User cancelled the invitation

class JobApplications(Base):
    __tablename__ = "job_applications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    senior_id: Mapped[str] = mapped_column(Text, ForeignKey('senior_users.id', ondelete='CASCADE'), nullable=False)
    
    status: Mapped[JobApplicationStatus] = mapped_column(Enum(JobApplicationStatus), default=JobApplicationStatus.PENDING, nullable=False)
    applied_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    responded_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Optional: Store additional info
    message: Mapped[str | None] = mapped_column(Text, nullable=True)  # Message from senior when applying/responding
    
    # Relationships
    job: Mapped["Jobs"] = relationship("Jobs", back_populates="applications")
    senior: Mapped["SeniorUsers"] = relationship("SeniorUsers", back_populates="job_applications")
    
class JobStatus(enum.Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_DONE = "payment_done"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
class Jobs(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.PROPOSED, nullable=False)
        
    user_id: Mapped[str | None] = mapped_column(Text, ForeignKey("users.id", ondelete="CASCADE"))
    
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    work_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    vehicle: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # location as json -> {"address": str, "latitude": float, "longitude": float}
    location: Mapped[dict | None] = mapped_column(JSON, nullable=True) 
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),  nullable=False)

    # ORM relationships
    user: Mapped["Users"] = relationship("Users", back_populates="job", uselist=False)
    applications: Mapped[list["JobApplications"]] = relationship("JobApplications", back_populates="job", cascade="all, delete-orphan")
    review: Mapped["Reviews"] = relationship("Reviews", back_populates="job", uselist=False)
    chat_room: Mapped["ChatRooms"] = relationship("ChatRooms", back_populates="job", uselist=False)
    
    # Helper property to get accepted seniors
    @property
    def accepted_seniors(self) -> list["SeniorUsers"]:
        """Get all seniors who have accepted this job"""
        return [app.senior for app in self.applications if app.status == JobApplicationStatus.ACCEPTED]
    
    # Helper property to get pending applications
    @property
    def pending_applications(self) -> list["JobApplications"]:
        """Get all pending applications for this job"""
        return [app for app in self.applications if app.status == JobApplicationStatus.PENDING]
    
    @property
    def declined_seniors(self) -> list["SeniorUsers"]:
        """Get all seniors who have declined this job"""
        return [app.senior for app in self.applications if app.status == JobApplicationStatus.DECLINED]
    
    @property
    def cancelled_seniors(self) -> list["SeniorUsers"]:
        """Get all seniors who have cancelled this job"""
        return [app.senior for app in self.applications if app.status == JobApplicationStatus.CANCELLED]