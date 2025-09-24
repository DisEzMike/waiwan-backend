from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..utils.schemas import JobPayload
from ..utils.deps import get_db, get_current_user

router = APIRouter(prefix="/job", tags=["job"])

@router.get("/{job_id}")
async def get_job(job_id: int, session: Session = Depends(get_db)):
    return job_id

@router.post("")
async def create_job(payload: JobPayload):
    payload.updated_at = datetime.now()
    return payload

@router.patch("")
async def update_job(payload: JobPayload):
    payload.updated_at = datetime.now()
    return payload