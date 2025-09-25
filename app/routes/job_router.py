from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from ..database.models.jobs import Jobs

from ..utils.schemas import JobPayload
from ..utils.deps import get_db, get_current_user

router = APIRouter(prefix="/job", tags=["job"])

@router.get("/{job_id}")
async def get_job(job_id: int, session: Session = Depends(get_db), ctx = Depends(get_current_user)):
    q = session.query(Jobs).where(Jobs.id == job_id)
    rows = q.all()
    return rows

@router.post("")
async def create_job(payload: JobPayload, session: Session = Depends(get_db), ctx = Depends(get_current_user)):
    user, _, _ = ctx
    payload.user_id = user.id
    payload.updated_at = datetime.now()
    
    q = session.query(Jobs).where(Jobs.senior_id == payload.senior_id and Jobs.status == 0)
    rows = q.all()
    
    if len(rows) > 1 : raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Seniors have started job.")
    
    job = Jobs(
        status=payload.status,
        user_id=payload.user_id,
        senior_id=payload.senior_id,
        title=payload.title,
        description=payload.description,
        price=payload.price,
        work_type=payload.work_type,
        vehicle=payload.vehicle,
    )
    
    session.add(job)
    session.flush()
    return job

@router.patch("")
async def update_job(payload: JobPayload, session: Session = Depends(get_db), ctx = Depends(get_current_user)):
    user, _, _ = ctx
    payload.user_id = user.id
    payload.updated_at = datetime.now()

    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    
    stmt = (
        update(Jobs)
        .where(Jobs.id == payload.id)
        .values(**data)
        .returning(Jobs)
    )
    q = session.scalars(stmt).one()
    return q