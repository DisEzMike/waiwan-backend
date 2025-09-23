from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.models.senior_users import SeniorUsers

def getUser_by_id(user_id: int, session: Session):
    user = session.execute(select(SeniorUsers).where(SeniorUsers.id == user_id)).scalars().first()
    return user

def getUser_by_ability_id(ability_id: int, session: Session):
    user = session.execute(select(SeniorUsers).where(SeniorUsers.ability_id == ability_id)).scalars().first()
    return user