from fastapi import APIRouter, Depends, HTTPException, status

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from ..utils.deps import get_current_user, get_db
from ..utils.schemas import AbilityOut, HeartbeatIn, MeResponse, ProfileOut, SearchPayload, UserOut

router = APIRouter(prefix="/search", tags=["search"])

@router.post("")
async def Search(payload: SearchPayload, ctx = Depends(get_current_user)):
    user, _, _ = ctx
    
    if user.role is not "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only senior_user can use a search")
    
    
    
    return {"keyword": payload.keyword, "user": user}