import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from ..database.redis import get_auth_code_data, get_auth_otp, set_auth_code_data, set_auth_otp

from ..utils.embedder import embed_query

from ..database.models.senior_users import SeniorAbilities, SeniorProfiles, SeniorUsers
from ..database.models.users import UserProfiles, Users
from ..utils.deps import get_db
from ..utils.jwt import create_access_token
from ..utils.schemas import CreateUserPayload, RequestOTP, RequestOTPResponse, TokenResponse, VerifyOTP, VerifyOTPResponse

router = APIRouter(prefix="/auth", tags=["auth"])

FIXED_OTP = "1234"

@router.post("/request-otp")
async def request_otp(payload: RequestOTP) -> RequestOTPResponse:
    otp = FIXED_OTP  # ใน production ต้องสร้าง OTP แบบสุ่มและส่งทาง SMS
    
    otp_exists = await get_auth_otp(payload.phone)
    if otp_exists is None:
        # บันทึก OTP ใน Redis พร้อม TTL (5 นาที)
        await set_auth_otp(payload.phone, otp)
    
    return RequestOTPResponse(message="ส่ง OTP ไปที่เบอร์โทรศัพท์เรียบร้อยแล้ว")

@router.post("/verify-otp")
async def verify_otp(payload: VerifyOTP, session=Depends(get_db)) -> VerifyOTPResponse:
    user_otp = await get_auth_otp(payload.phone)
    if payload.otp != user_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP ไม่ถูกต้อง")

    if payload.role not in ["user", "senior_user"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    
    if payload.role == "user":
        stmt = select(UserProfiles).where(UserProfiles.phone == payload.phone)
        profile = session.scalars(stmt).first()
        
        user: Users | None = None
        if profile:
            # Existing user
            user = session.execute(select(Users).where(Users.profile_id == profile.id)).scalars().first()
    elif payload.role == "senior_user":
        stmt = select(SeniorProfiles).where(SeniorProfiles.phone == payload.phone)
        profile = session.scalars(stmt).first()
        
        user: SeniorUsers | None = None
        if profile:
            user = session.execute(select(SeniorUsers).where(SeniorUsers.profile_id == profile.id)).scalars().first()

    auth_code = secrets.token_hex(16)
    data = {
        "phone": payload.phone,
        "role": payload.role,
        "is_new": user is None
    }
    await set_auth_code_data(auth_code, data)
    return VerifyOTPResponse(is_new=data['is_new'], auth_code=auth_code)
    
@router.post("", response_model=TokenResponse)
async def create_user(auth_code: str, payload: CreateUserPayload, session=Depends(get_db)) -> TokenResponse:
    auth_data = await get_auth_code_data(auth_code)
    if auth_data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Auth Code ไม่ถูกต้อง")
    
    phone = auth_data['phone']
    role = auth_data['role']
    
    if auth_data['is_new'] == False:
        user: Users | SeniorUsers | None = None
        if role == "user":
            user = session.execute(select(Users).where(Users.profile.has(phone=phone))).scalars().first()
            if user is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")
                    
        elif role == "senior_user":
            user = session.execute(select(SeniorUsers).where(SeniorUsers.profile.has(phone=phone))).scalars().first()
            if user is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")
    else:
        if role == "user":
            data = payload.profile.model_dump(exclude_unset=True, exclude_none=True)
            profile = UserProfiles(**data)
            session.add(profile)
            session.flush()
            
            user = Users(
                displayname=f"{payload.profile.first_name} {payload.profile.last_name}",
                profile_id=profile.id
            )
            session.add(user)
            session.flush()
        elif role == "senior_user":
            data = payload.profile.model_dump(exclude_unset=True, exclude_none=True)
            profile = SeniorProfiles(**data)
            session.add(profile)
            session.flush()
            
            data = payload.ability.model_dump(exclude_unset=True, exclude_none=True)
            ability = SeniorAbilities(
                **data,
                embedding=embed_query(" ".join([payload.ability.work_experience or "", payload.ability.other_ability or ""]))
                # file_id=payload.file_id,
            )
            session.add(ability)
            session.flush()
            
            user = SeniorUsers(
                displayname=f"{payload.profile.first_name} {payload.profile.last_name}",
                profile_id=profile.id,
                ability_id=ability.id
            )
            session.add(user)
            session.flush()
                    
    return TokenResponse(
        access_token=create_access_token(sub=str(user.id), extra={"phone": phone, "role": role}),
        user_id=user.id,
        role=role,
        profile_id=user.profile_id,
        ability_id=getattr(user, 'ability_id', None)
    )    