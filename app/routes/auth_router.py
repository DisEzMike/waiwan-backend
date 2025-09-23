from fastapi import APIRouter, Depends, HTTPException
from scipy import stats
from sqlalchemy import select

from ..utils.embedder import embed_query

from ..database.models.senior_users import SeniorAbilities, SeniorProfiles, SeniorUsers
from ..database.models.users import UserProfiles, Users
from ..utils.deps import get_db
from ..utils.jwt import create_access_token
from ..utils.schemas import RequestOTP, TokenResponse, VerifyOTP

router = APIRouter(prefix="/auth", tags=["auth"])

FIXED_OTP = "1234"

@router.post("/request-otp")
async def request_otp(payload: RequestOTP):
    return {"message": "OTP sent"}

@router.post("/verify-otp")
async def verify_otp(payload: VerifyOTP, session=Depends(get_db)):
    FIXED_OTP = "1234"
    if payload.otp != FIXED_OTP:
        raise HTTPException(status_code=stats.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    if payload.role not in ["user", "senior_user"]:
        raise HTTPException(status_code=stats.HTTP_400_BAD_REQUEST, detail="Invalid role")
    
    if payload.role == "user":
        stmt = select(UserProfiles).where(UserProfiles.phone == payload.phone)
        profile = session.scalars(stmt).first()
        
        user: Users | None = None
        if profile:
            # Existing user
            user = session.execute(select(Users).where(Users.profile_id == int(profile.id))).scalars().first()
        else:
            # New user
            profile = UserProfiles(
                first_name=payload.first_name,
                last_name=payload.last_name,
                phone=payload.phone,
                gender=payload.gender
            )
    
            session.add(profile)
            session.flush()
            
            user = Users(
                displayname= f"{payload.first_name} {payload.last_name}",
                profile_id=profile.id
            )
            session.add(user)
            session.flush()
    elif payload.role == "senior_user":
        stmt = select(SeniorProfiles).where(SeniorProfiles.phone == payload.phone)
        profile = session.scalars(stmt).first()
        
        user: SeniorUsers | None = None
        if profile:
            # Existing user
            user = session.execute(select(SeniorUsers).where(SeniorUsers.profile_id == int(profile.id))).scalars().first()
        else:
            # New user
            profile = SeniorProfiles(
                first_name=payload.first_name,
                last_name=payload.last_name,
                id_card=payload.id_card,
                addr_from_id=payload.addr_form_id,
                addr_current=payload.addr_current,
                underlying_diseases=payload.underlying_disease,
                contact_person=payload.contact_person,
                contact_phone=payload.contact_phone,
                phone=payload.phone,
                gender=payload.gender
            )
            session.add(profile)
            session.flush()
            
            embedding = embed_query(" ".join([payload.career, payload.other_ability]))
            ability = SeniorAbilities(
                type=payload.type,
                career=payload.career,
                other_ability=payload.other_ability,
                vehicle=payload.vihecle,
                offsite_work=payload.offsite_work,
                embedding=embedding
                # file_id=payload.file_id,
            )
            session.add(ability)
            session.flush()
            user = SeniorUsers(
                displayname=f"{payload.first_name} {payload.last_name}",
                profile_id=profile.id,
                ability_id=ability.id
            )
            session.add(user)
            session.flush()
                        
    token = create_access_token(sub=str(user.id), extra={"phone": payload.phone, "role": payload.role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        role=payload.role,
        profile_id=user.profile_id,
        ability_id=user.ability_id if payload.role == "senior_user" else None,
    )