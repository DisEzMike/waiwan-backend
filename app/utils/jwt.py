from __future__ import annotations
import time
from typing import Any, Dict, Optional
import jwt
from .config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRES_MINUTES, JWT_ISSUER

def create_access_token(sub: str, extra: Optional[Dict[str, Any]] = None) -> str:
    now = int(time.time())
    payload: Dict[str, Any] = {
        "iss": JWT_ISSUER,
        "iat": now,
        "nbf": now,
        "exp": now + JWT_EXPIRES_MINUTES * 60,
        "sub": sub,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"require": ["exp", "iat", "nbf", "sub"]})