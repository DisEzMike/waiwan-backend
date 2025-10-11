"""
Job Application Service - Handles senior acceptance workflow
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import Optional

from app.database.models.jobs import Jobs, JobApplications, JobApplicationStatus
from app.database.models.senior_users import SeniorUsers
from app.database.models.chats import ChatRooms


class JobApplicationService:
    
    @staticmethod
    def invite_senior_to_job(session: Session, job_id: int, senior_id: str, message: str = None) -> JobApplications:
        """Invite a senior to apply for a job"""
        
        # Check if already applied
        existing = session.query(JobApplications).filter(
            and_(JobApplications.job_id == job_id, JobApplications.senior_id == senior_id)
        ).first()
        
        if existing:
            if existing.status == JobApplicationStatus.PENDING:
                raise ValueError("Senior already has a pending application for this job")
            elif existing.status == JobApplicationStatus.ACCEPTED:
                raise ValueError("Senior already accepted this job")
            # If declined or cancelled, allow new application
            existing.status = JobApplicationStatus.PENDING
            existing.applied_at = datetime.utcnow()
            existing.responded_at = None
            existing.message = message
            return existing
        
        # Create new application
        application = JobApplications(
            job_id=job_id,
            senior_id=senior_id,
            status=JobApplicationStatus.PENDING,
            message=message
        )
        session.add(application)
        return application
    
    @staticmethod
    def accept_job(session: Session, job_id: int, senior_id: str, message: str = None) -> JobApplications:
        """Senior accepts a job invitation"""
        
        application = session.query(JobApplications).filter(
            and_(
                JobApplications.job_id == job_id, 
                JobApplications.senior_id == senior_id,
                JobApplications.status == JobApplicationStatus.PENDING
            )
        ).first()
        
        if not application:
            raise ValueError("No pending application found for this job and senior")
        
        application.status = JobApplicationStatus.ACCEPTED
        application.responded_at = datetime.utcnow()
        if message:
            application.message = message
        
        # Update job status to ACCEPTED when first senior accepts
        job = session.query(Jobs).filter(Jobs.id == job_id).first()
        if job:
            from app.database.models.jobs import JobStatus
            if job.status == JobStatus.PROPOSED:
                job.status = JobStatus.ACCEPTED
            
            # Create chat room if it doesn't exist
            if not job.chat_room:
                chat_room = ChatRooms(
                    job_id=job_id,
                    user_id=job.user_id
                )
                session.add(chat_room)
        
        return application
    
    @staticmethod
    def decline_job(session: Session, job_id: int, senior_id: str, message: str = None) -> JobApplications:
        """Senior declines a job invitation"""
        
        application = session.query(JobApplications).filter(
            and_(
                JobApplications.job_id == job_id, 
                JobApplications.senior_id == senior_id,
                JobApplications.status == JobApplicationStatus.PENDING
            )
        ).first()
        
        if not application:
            raise ValueError("No pending application found for this job and senior")
        
        application.status = JobApplicationStatus.DECLINED
        application.responded_at = datetime.utcnow()
        if message:
            application.message = message
        
        return application
    
    @staticmethod
    def cancel_invitation(session: Session, job_id: int, senior_id: str) -> JobApplications:
        """User cancels a job invitation"""
        
        application = session.query(JobApplications).filter(
            and_(
                JobApplications.job_id == job_id, 
                JobApplications.senior_id == senior_id,
                JobApplications.status == JobApplicationStatus.PENDING
            )
        ).first()
        
        if not application:
            raise ValueError("No pending application found for this job and senior")
        
        application.status = JobApplicationStatus.CANCELLED
        application.responded_at = datetime.utcnow()
        
        return application
    
    @staticmethod
    def get_pending_applications_for_senior(session: Session, senior_id: str) -> list[JobApplications]:
        """Get all pending job applications for a senior"""
        return session.query(JobApplications).filter(
            and_(
                JobApplications.senior_id == senior_id,
                JobApplications.status == JobApplicationStatus.PENDING
            )
        ).all()
    
    @staticmethod
    def get_accepted_jobs_for_senior(session: Session, senior_id: str) -> list[Jobs]:
        """Get all jobs accepted by a senior"""
        applications = session.query(JobApplications).filter(
            and_(
                JobApplications.senior_id == senior_id,
                JobApplications.status == JobApplicationStatus.ACCEPTED
            )
        ).all()
        return [app.job for app in applications]
    
    @staticmethod
    def can_access_chatroom(session: Session, chat_room_id: str, senior_id: str) -> bool:
        """Check if senior can access a chatroom (must have accepted the job)"""
        chat_room = session.query(ChatRooms).filter(ChatRooms.id == chat_room_id).first()
        if not chat_room:
            return False
        
        # Check if senior has accepted the job
        application = session.query(JobApplications).filter(
            and_(
                JobApplications.job_id == chat_room.job_id,
                JobApplications.senior_id == senior_id,
                JobApplications.status == JobApplicationStatus.ACCEPTED
            )
        ).first()
        
        return application is not None