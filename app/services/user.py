from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.redis import set_presence_and_loc

from ..database.models.senior_users import SeniorAbilities, SeniorProfiles, SeniorUsers

def getUser_by_id(user_id: str, session: Session):
    user = session.execute(select(SeniorUsers).where(SeniorUsers.id == user_id)).scalars().first()
    return user

def getUser_by_ability_id(ability_id: str, session: Session):
    user = session.execute(select(SeniorUsers).where(SeniorUsers.ability_id == ability_id)).scalars().first()
    return user

def getProfile_by_id(profile_id: str, session: Session):
    user_profile = session.execute(select(SeniorProfiles).where(SeniorProfiles.id == profile_id)).scalars().first()
    return user_profile

def getAbility_by_id(ability_id: str, session: Session):
    user_ability = session.execute(select(SeniorAbilities).where(SeniorAbilities.id == ability_id)).scalars().first()
    return user_ability

async def set_online(user: SeniorUsers, lat: float, lng: float, ttl: int):
    try:
        await set_presence_and_loc(
            provider_id=user.id,
            lat=lat,
            lng=lng,
            # accuracy=payload.accuracy,
            ttl=ttl,
        )
    except Exception as e:
        print(e)
    return