from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.redis import set_presence_and_loc

from ..utils.config import PRESENCE_TTL_SECONDS

from ..database.models.senior_users import SeniorUsers

def getUser_by_id(user_id: int, session: Session):
    user = session.execute(select(SeniorUsers).where(SeniorUsers.id == user_id)).scalars().first()
    return user

def getUser_by_ability_id(ability_id: int, session: Session):
    user = session.execute(select(SeniorUsers).where(SeniorUsers.ability_id == ability_id)).scalars().first()
    return user

async def set_online(user: SeniorUsers, lat: float, lng: float, ttl: int):
    try:
        await set_presence_and_loc(
            provider_id=user.id,
            lat=lat,
            lng=lng,
            # accuracy=payload.accuracy,
            ttl=PRESENCE_TTL_SECONDS,
        )
    except Exception as e:
        print(e)
    return