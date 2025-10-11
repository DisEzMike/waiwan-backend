"""
Job Application Router - API endpoints for job acceptance workflow
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import update
from pydantic import BaseModel
from typing import Optional

from app.utils.deps import get_current_user, get_db
from app.services.job_application import JobApplicationService
from app.database.models.jobs import Jobs, JobApplications, JobApplicationStatus, JobStatus
from app.utils.schemas import JobPayload

router = APIRouter(prefix="/jobs", tags=["jobs"])  # Changed prefix to /jobs

class JobApplicationResponse(BaseModel):
    id: int
    job_id: int
    senior_id: str
    status: str
    applied_at: str
    responded_at: Optional[str]
    message: Optional[str]

class InviteSeniorRequest(BaseModel):
    senior_id: str
    message: Optional[str] = None

class RespondToJobRequest(BaseModel):
    message: Optional[str] = None

class JobResponse(BaseModel):
    id: int
    status: str
    user_id: str
    title: Optional[str]
    description: Optional[str]
    price: Optional[float]
    work_type: Optional[str]
    vehicle: Optional[bool]
    created_at: str
    applications_count: int
    accepted_seniors_count: int
    chat_room_id: Optional[str]

# ===== JOB MANAGEMENT ENDPOINTS =====

@router.get("/{job_id}")
async def get_job(
    job_id: int, 
    session: Session = Depends(get_db), 
    ctx=Depends(get_current_user)
):
    """Get job details with applications and chat room info"""
    user, _, _ = ctx
    
    job = session.get(Jobs, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    # Check if user has access to this job
    if user.role == "user" and job.user_id != user.id:
        # Only job owner can see job details
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif user.role == "senior_user":
        # Senior can see if they have application for this job
        has_application = session.query(JobApplications).filter(
            JobApplications.job_id == job_id,
            JobApplications.senior_id == user.id
        ).first()
        if not has_application:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return {
        "id": job.id,
        "status": job.status.value,
        "user_id": job.user_id,
        "title": job.title,
        "description": job.description,
        "price": job.price,
        "work_type": job.work_type,
        "vehicle": job.vehicle,
        "applications": [
            {
                "id": app.id,
                "senior_id": app.senior_id,
                "senior_name": app.senior.displayname if app.senior else "Unknown",
                "status": app.status.value,
                "applied_at": app.applied_at.isoformat(),
                "responded_at": app.responded_at.isoformat() if app.responded_at else None,
                "message": app.message
            }
            for app in job.applications
        ],
        "accepted_seniors": [
            {
                "id": senior.id,
                "displayname": senior.displayname
            }
            for senior in job.accepted_seniors
        ],
        "chat_room": {
            "id": job.chat_room.id,
            "is_active": job.chat_room.is_active
        } if job.chat_room else None
    }

@router.post("")
async def create_job(
    payload: JobPayload, 
    session: Session = Depends(get_db), 
    ctx=Depends(get_current_user)
):
    """Create a new job"""
    user, _, _ = ctx
    
    if user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only users can create jobs"
        )
    
    # Create the job
    job = Jobs(
        status=JobStatus.PROPOSED,  # Always start as PROPOSED
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        price=payload.price,
        work_type=payload.work_type,
        vehicle=payload.vehicle,
    )
    
    session.add(job)
    session.flush()
    session.commit()
    
    return {
        "message": "Job created successfully",
        "job": {
            "id": job.id,
            "status": job.status.value,
            "user_id": job.user_id,
            "title": job.title,
            "description": job.description,
            "price": job.price,
            "work_type": job.work_type,
            "vehicle": job.vehicle
        }
    }

@router.patch("/{job_id}")
async def update_job(
    job_id: int,
    payload: JobPayload, 
    session: Session = Depends(get_db), 
    ctx=Depends(get_current_user)
):
    """Update an existing job"""
    user, _, _ = ctx
    
    if user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only users can update jobs"
        )
    
    # Get the job
    job = session.get(Jobs, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    # Check ownership
    if job.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You can only update your own jobs"
        )
    
    # Update job fields
    update_data = payload.model_dump(exclude_unset=True, exclude_none=True, exclude={'id'})
    
    for field, value in update_data.items():
        setattr(job, field, value)
    
    session.commit()
    
    return {
        "message": "Job updated successfully",
        "job": {
            "id": job.id,
            "status": job.status.value,
            "user_id": job.user_id,
            "title": job.title,
            "description": job.description,
            "price": job.price,
            "work_type": job.work_type,
            "vehicle": job.vehicle
        }
    }

# ===== JOB APPLICATION ENDPOINTS =====

@router.post("/{job_id}/invite")
async def invite_senior_to_job(
    job_id: int,
    request: InviteSeniorRequest,
    ctx=Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """User invites a senior to apply for their job"""
    user, _, _ = ctx
    
    if user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only users can invite seniors to jobs"
        )
    
    try:
        application = JobApplicationService.invite_senior_to_job(
            session=session,
            job_id=job_id,
            senior_id=request.senior_id,
            message=request.message
        )
        session.commit()
        
        return {
            "message": "Senior invited successfully",
            "application_id": application.id
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{job_id}/accept")
async def accept_job_invitation(
    job_id: int,
    request: RespondToJobRequest,
    ctx=Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Senior accepts a job invitation"""
    user, _, _ = ctx
    
    if user.role != "senior_user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only senior users can accept job invitations"
        )
    
    try:
        application = JobApplicationService.accept_job(
            session=session,
            job_id=job_id,
            senior_id=user.id,
            message=request.message
        )
        session.commit()
        
        return {
            "message": "Job accepted successfully",
            "application_id": application.id,
            "chat_room_created": True
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{job_id}/decline")
async def decline_job_invitation(
    job_id: int,
    request: RespondToJobRequest,
    ctx=Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Senior declines a job invitation"""
    user, _, _ = ctx
    
    if user.role != "senior_user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only senior users can decline job invitations"
        )
    
    try:
        application = JobApplicationService.decline_job(
            session=session,
            job_id=job_id,
            senior_id=user.id,
            message=request.message
        )
        session.commit()
        
        return {
            "message": "Job declined",
            "application_id": application.id
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/my-jobs")
async def get_my_jobs(
    ctx=Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Get all jobs created by current user"""
    user, _, _ = ctx
    
    if user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only users can view their jobs"
        )
    
    jobs = session.query(Jobs).filter(Jobs.user_id == user.id).all()
    
    return {
        "count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "status": job.status.value,
                "title": job.title,
                "description": job.description,
                "price": job.price,
                "work_type": job.work_type,
                "vehicle": job.vehicle,
                "applications_count": len(job.applications),
                "accepted_seniors_count": len(job.accepted_seniors),
                "pending_applications_count": len(job.pending_applications),
                "chat_room_id": job.chat_room.id if job.chat_room else None
            }
            for job in jobs
        ]
    }

@router.get("/applications/pending")
async def get_pending_applications(
    ctx=Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Get all pending job applications for current senior"""
    user, _, _ = ctx
    
    if user.role != "senior_user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only senior users can view their applications"
        )
    
    applications = JobApplicationService.get_pending_applications_for_senior(
        session=session,
        senior_id=user.id
    )
    
    return {
        "count": len(applications),
        "applications": [
            {
                "id": app.id,
                "job_id": app.job_id,
                "job_title": app.job.title,
                "job_description": app.job.description,
                "job_price": app.job.price,
                "applied_at": app.applied_at.isoformat(),
                "message": app.message
            }
            for app in applications
        ]
    }

@router.get("/applications/accepted")
async def get_accepted_jobs(
    ctx=Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Get all jobs accepted by current senior"""
    user, _, _ = ctx
    
    if user.role != "senior_user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only senior users can view their accepted jobs"
        )
    
    jobs = JobApplicationService.get_accepted_jobs_for_senior(
        session=session,
        senior_id=user.id
    )
    
    return {
        "count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "price": job.price,
                "work_type": job.work_type,
                "vehicle": job.vehicle,
                "user_id": job.user_id,
                "chat_room_id": job.chat_room.id if job.chat_room else None
            }
            for job in jobs
        ]
    }

@router.get("/{job_id}/flow-test")
async def test_flow(
    job_id: int,
    ctx=Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Test endpoint to verify the complete flow"""
    user, _, _ = ctx
    
    from app.database.models.jobs import Jobs, JobStatus
    
    job = session.get(Jobs, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    # Get job applications
    applications = session.query(JobApplications).filter(JobApplications.job_id == job_id).all()
    
    # Get chat room
    chat_room = job.chat_room
    
    return {
        "job": {
            "id": job.id,
            "title": job.title,
            "status": job.status.value,
            "user_id": job.user_id
        },
        "applications": [
            {
                "id": app.id,
                "senior_id": app.senior_id,
                "status": app.status.value,
                "applied_at": app.applied_at.isoformat(),
                "responded_at": app.responded_at.isoformat() if app.responded_at else None
            }
            for app in applications
        ],
        "chat_room": {
            "id": chat_room.id,
            "is_active": chat_room.is_active,
            "accepted_seniors_count": len(chat_room.accepted_seniors)
        } if chat_room else None,
        "flow_status": {
            "can_chat": job.status in [JobStatus.ACCEPTED, JobStatus.IN_PROGRESS],
            "accepted_seniors": len(job.accepted_seniors),
            "pending_applications": len(job.pending_applications)
        }
    }