from fastapi import APIRouter, Depends, HTTPException, status

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from ..database.models.senior_users import SeniorAbilities, SeniorProfiles, SeniorUsers

from ..services.user import getAbility_by_id, getProfile_by_id, getUser_by_id, set_online

from ..utils.deps import get_current_user, get_db
from ..utils.schemas import AbilityOut, HeartbeatIn, UserResponse, ProfileOut, UserOut

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me",  response_model=UserResponse)
def get_me(ctx = Depends(get_current_user), session: Session = Depends(get_db)):
    user, profile, ability = ctx
    return UserResponse(
        user=UserOut(
            id=user.id,
            role=user.role,
            displayname=user.displayname,
            profile_id=user.profile_id,
            ability_id=user.ability_id if user.role == "senior_user" else None,
            created_at=user.created_at
        ),
        profile=ProfileOut(
            id=profile.id,
            first_name=profile.first_name,
            last_name=profile.last_name,
            id_card=profile.id_card if user.role == "senior_user" else None,
            addr_from_id=profile.addr_from_id if user.role == "senior_user" else None,
            addr_current=profile.addr_current if user.role == "senior_user" else None,
            phone=profile.phone,
            gender=profile.gender,
            underlying_diseases=profile.underlying_diseases if user.role == "senior_user" else None,
            contact_person=profile.contact_person if user.role == "senior_user" else None,
            contact_phone=profile.contact_phone if user.role == "senior_user" else None,
        ),
        ability=(AbilityOut(
            id=ability.id,
            type=ability.type,
            career=ability.career,
            other_ability=ability.other_ability,
            vehicle=ability.vehicle,
            offsite_work=ability.offsite_work 
        ) if ability else None)
    )

@router.patch("")
async def update_me(
    payload: UserResponse,
    ctx = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Update current user, profile, ability"""
    user, profile, ability = ctx
    if payload.user:
        if payload.user.displayname:
            user.displayname = payload.user.displayname
        session.add(user)
    
    if payload.profile:
        db_profile = None
        if user.role == "user":
            db_profile = session.get(SeniorProfiles, user.profile_id)
        elif user.role == "senior_user":
            db_profile = session.get(SeniorProfiles, user.profile_id)
        
        if db_profile:
            if payload.profile.first_name:
                db_profile.first_name = payload.profile.first_name
            if payload.profile.last_name:
                db_profile.last_name = payload.profile.last_name
            if user.role == "senior_user":
                if payload.profile.id_card:
                    db_profile.id_card = payload.profile.id_card
                if payload.profile.addr_from_id:
                    db_profile.addr_from_id = payload.profile.addr_from_id
                if payload.profile.addr_current:
                    db_profile.addr_current = payload.profile.addr_current
                if payload.profile.underlying_diseases:
                    db_profile.underlying_diseases = payload.profile.underlying_diseases
                if payload.profile.contact_person:
                    db_profile.contact_person = payload.profile.contact_person
                if payload.profile.contact_phone:
                    db_profile.contact_phone = payload.profile.contact_phone
                if payload.profile.gender:
                    db_profile.gender = payload.profile.gender
            if payload.profile.phone:
                db_profile.phone = payload.profile.phone

@router.get("/{user_id}")
async def get_user(user_id: str, ctx = Depends(get_current_user), session: Session = Depends(get_db)):
    user: SeniorUsers | None = getUser_by_id(user_id, session)
    if user is None : raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    profile: SeniorProfiles = user.profile
    ability: SeniorAbilities = user.ability
    return UserResponse(
        user=UserOut(
            id=user.id,
            role="senior_user",
            displayname=user.displayname,
            profile_id=user.profile_id,
            ability_id=user.ability_id,
            created_at=user.created_at
        ),
        profile=ProfileOut(
            id=profile.id,
            first_name=profile.first_name,
            last_name=profile.last_name,
            id_card=profile.id_card,
            addr_from_id=profile.addr_from_id,
            addr_current=profile.addr_current,
            phone=profile.phone,
            gender=profile.gender,
            underlying_diseases=profile.underlying_diseases,
            contact_person=profile.contact_person,
            contact_phone=profile.contact_phone,
        ),
        ability=AbilityOut(
            id=ability.id,
            type=ability.type,
            career=ability.career,
            other_ability=ability.other_ability,
            vehicle=ability.vehicle,
            offsite_work=ability.offsite_work 
        )
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

