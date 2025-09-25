from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
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
    user_id: str
    role: str
    profile_id: Optional[str] = None
    ability_id: Optional[str] = None

# ---------- Users / Profiles / Abilities ----------
class UserOut(BaseModel):
    id: str
    role: Optional[str] = None
    displayname: Optional[str] = None
    profile_id: Optional[str] = None
    ability_id: Optional[str] = None
    created_at: datetime = None

class ProfileOut(BaseModel):
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    id_card: Optional[str] = None
    addr_from_id: Optional[str] = None
    addr_current: Optional[str] = None
    phone: str
    gender: Optional[str] = None
    underlying_diseases: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None

class AbilityOut(BaseModel):
    id: str
    type: Optional[str] = None
    career: Optional[str] = None
    other_ability: Optional[str] = None
    vehicle: Optional[bool] = None
    offsite_work: Optional[bool] = None
    file_id: Optional[str] = None
    embedding: Optional[List[float]] = None

class UserResponse(BaseModel):
    user: UserOut
    profile: Optional[ProfileOut] = None
    ability: Optional[AbilityOut] = None

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
    top_k: int = 20
    range: int = 10000 # 10km

class SearchOut(BaseModel):
    count: int
    list: list
    
# ---------- Job ----------
class JobPayload(BaseModel):
    id: Optional[int] = None
    status: Optional[int] = None
    user_id: Optional[str] = None
    senior_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    work_type: Optional[str] = None
    vehicle: Optional[bool] = None
    updated_at: Optional[datetime] = None

# ---------- Chat ----------
class ChatMessageCreate(BaseModel):
    message: str = Field(..., description="Message content")

class ChatMessageOut(BaseModel):
    id: str
    room_id: str
    sender_id: str
    sender_type: str  # "user" or "senior_user"
    sender_name: Optional[str] = None
    message: str
    is_read: bool
    created_at: datetime

class ChatRoomOut(BaseModel):
    id: str
    job_id: int
    user_id: str
    senior_id: str
    user_name: Optional[str] = None
    senior_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    unread_count: Optional[int] = None
    last_message: Optional[ChatMessageOut] = None

class ChatRoomWithMessages(ChatRoomOut):
    messages: List[ChatMessageOut] = []

# ---------- WebSocket Message Types ----------
class WSMessage(BaseModel):
    type: str = Field(..., description="Message type: 'message', 'typing', 'mark_read'")

class WSChatMessage(WSMessage):
    type: str = "message"
    message: str = Field(..., description="Message content")

class WSTypingIndicator(WSMessage):
    type: str = "typing"
    is_typing: bool = Field(..., description="Whether user is typing")

class WSMarkRead(WSMessage):
    type: str = "mark_read"

# ---------- File Upload ----------
class FileUploadResponse(BaseModel):
    id: int = Field(..., description="File ID")
    filename: str = Field(..., description="Generated filename")
    original_filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="File storage path")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    upload_url: str = Field(..., description="URL to access the file")
    created_at: datetime = Field(..., description="Upload timestamp")
    is_profile_image: bool = Field(False, description="Whether file is set as profile image")

class FileOut(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    file_url: str = Field(..., description="URL to access the file")
    upload_date: datetime = Field(..., description="Upload timestamp")
    is_active: bool
    
    class Config:
        from_attributes = True