from fastapi import APIRouter, Depends, HTTPException, status

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from ..services.user import set_online

from ..utils.deps import get_current_user, get_db
from ..utils.schemas import AbilityOut, HeartbeatIn, MeResponse, ProfileOut, UserOut

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me",  response_model=MeResponse)
def get_me(ctx = Depends(get_current_user), session: Session = Depends(get_db)):
    user, profile, ability = ctx
    return MeResponse(
        user=UserOut(
            id=user.id,
            role=user.role,
            displayname=user.displayname,
            profile_id=user.profile_id,
            ability_id=user.ability_id if ability else None,
        ),
        profile=(ProfileOut(
            id=profile.id,
            first_name=profile.first_name,
            last_name=profile.last_name,
            phone=profile.phone,
            gender=profile.gender
        ) if profile else None),
        ability=(AbilityOut(
            id=ability.id,
            career=ability.career,
            other_ability=ability.other_ability
        ) if ability else None),
    ) 
    

@router.post("/set-online", status_code=status.HTTP_204_NO_CONTENT)
async def heartbeat(
    payload: HeartbeatIn,
    ctx = Depends(get_current_user),
):
    user, _, _ = ctx
    if user.role != "senior_user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only senior_user can send heartbeat")
    
    from ..database.redis import PRESENCE_TTL_SECONDS
    await set_online(user, payload.lat, payload.lng, PRESENCE_TTL_SECONDS)

    return

