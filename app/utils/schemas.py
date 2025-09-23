from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field

# ---------- Auth ----------
class RequestOTP(BaseModel):
    phone: str

class VerifyOTP(BaseModel):
    phone: str
    otp: str = Field(..., description="fixed 1234")
    role: str = Field(..., description='"user" | "senior_user"')

    # สมัครสมาชิกครั้งแรก (optional)
    displayname: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    id_card: Optional[str] = None
    addr_form_id: Optional[str] = None
    addr_current: Optional[str] = None
    underlying_disease: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    gender: Optional[str] = None
    
    type: Optional[str] = None
    career: Optional[str] = None
    other_ability: Optional[str] = None
    vihecle: Optional[bool] = None
    offsite_work: Optional[bool] = None
    # file_id: Optional[int] = None
    # embedding: Optional[List[float]] = None  # ต้องยาว 384 ถ้าส่งมา

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    profile_id: Optional[int] = None
    ability_id: Optional[int] = None

# ---------- Users / Profiles / Abilities ----------
class UserOut(BaseModel):
    id: int
    role: str
    displayname: Optional[str] = None
    profile_id: Optional[int] = None
    ability_id: Optional[int] = None

class ProfileOut(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: str
    gender: Optional[str] = None

class AbilityOut(BaseModel):
    id: int
    career: Optional[str] = None
    other_ability: Optional[str] = None

class AbilityUpdateEmbedding(BaseModel):
    embedding: List[float] = Field(..., min_length=384, max_length=384)

class MeResponse(BaseModel):
    user: UserOut
    profile: Optional[ProfileOut] = None
    ability: Optional[AbilityOut] = None

# ---------- Vector Search ----------
class AbilitySearchPayload(BaseModel):
    embedding: List[float] = Field(..., min_length=384, max_length=384)
    top_k: int = 5
    metric: str = Field(default="cosine", description='"cosine" | "l2" | "ip"')
    normalize_query: bool = True

# ---------- Heartbeat ----------
class HeartbeatIn(BaseModel):
    lat: float = Field(..., description="Latitude in decimal degrees")
    lng: float = Field(..., description="Longitude in decimal degrees")
    # accuracy: float | None = Field(None, description="GPS accuracy (meters)")
    
# ---------- Search ----------
class SearchPayload(BaseModel):
    keyword: str = Field(..., description="Keyword to find a work")
    lat: float = Field(..., description="Latitude in decimal degrees")
    lng: float = Field(..., description="Longitude in decimal degrees")