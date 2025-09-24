from __future__ import annotations
from typing import Generator, Optional, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database.db import db as DBInstance
from .jwt import decode_token
from ..database.models.users import Users, UserProfiles
from ..database.models.senior_users import SeniorUsers, SeniorProfiles, SeniorAbilities

security = HTTPBearer(auto_error=True)

def get_db() -> Generator[Session, None, None]:
    with DBInstance.session() as session:
        yield session

def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db),
) -> Tuple[Users | SeniorUsers, Optional[UserProfiles | SeniorUsers], Optional[SeniorAbilities]]:
    token = cred.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user: Users | SeniorUsers | None = None
    if payload.get("role") == "user":
        user = session.get(Users, int(sub))
    elif payload.get("role") == "senior_user":
        user = session.get(SeniorUsers, int(sub))
        
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    profile: UserProfiles | SeniorProfiles = user.profile
    ability: SeniorAbilities | None = user.ability if payload.get("role") == "senior_user" else None
     
    user.role = payload.get("role") 
    
    return (user, profile, ability)