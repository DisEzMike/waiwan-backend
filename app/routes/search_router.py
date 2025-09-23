from fastapi import APIRouter, Depends, HTTPException, status

from fastapi.concurrency import run_in_threadpool
from numpy import sort
from sqlalchemy.orm import Session

from ..utils.score import setScore

from ..services.user import getUser_by_ability_id, getUser_by_id

from ..database.redis import get_loc, get_locations_batch, online_ids

from ..database.models.senior_users import SeniorAbilities

from ..utils.embedder import embed_query

from ..utils.deps import get_current_user, get_db
from ..utils.schemas import AbilityOut, HeartbeatIn, MeResponse, ProfileOut, SearchPayload, UserOut

router = APIRouter(prefix="/search", tags=["search"])

@router.post("")
async def Search(payload: SearchPayload, ctx = Depends(get_current_user), session: Session = Depends(get_db)):
    user, _, _ = ctx
    
    if user.role != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Only user can use a search -> {user.role}")
    
    query = payload.keyword
    # lat = payload.lat
    # lng = payload.lng
    lat = 13.7540
    lng = 100.5014
    k = payload.top_k
    
    online_list = await online_ids()
    
    qvec = embed_query(query)
    q = (
            session.query(
                SeniorAbilities, 
                1 - SeniorAbilities.embedding.cosine_distance(qvec).label("sim")
            )
            .where(SeniorAbilities.id.in_(online_list))
            .order_by(SeniorAbilities.embedding.cosine_distance(qvec))
            .limit(k)
        )
    rows = q.all()
    
    out = []
    for r,sim in rows:
        print(r)
        user = getUser_by_ability_id(r.id, session)
        location = await get_loc(user.id)
        
        if location is None:
            pass
        
        from haversine import haversine
        
        dist = haversine((lat, lng),(location['lat'], location['lng']), unit="m")
        
        score = setScore(sim, dist, 0.7)
        data = {
            "id": user.id,
            "type": r.type,
            "career": r.career,
            "other_ability": r.other_ability,
            "vehicle": r.vehicle,
            "offsite_work": r.offsite_work,
            "score": score,
            "distance": dist
        }
        
        
        out.append(data)
    def over05(x):
        return x['score'] >= 0.5
    def below05(x):
        return x['score'] < 0.5
    out_over05 = sorted(list(filter(over05, out)), key=lambda x: x['score'], reverse=True)
    out_below05 = sorted(list(filter(below05, out)), key=lambda x: x['distance'])
    return out_over05 + out_below05