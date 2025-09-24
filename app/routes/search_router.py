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
    lat = payload.lat
    lng = payload.lng
    k = payload.top_k
    range = payload.range
    
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
        
        score = setScore(sim, dist, 0.7, range)
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
    def range_filter(x):
        return x['distance'] <= range
    filtered_out = list(filter(range_filter, out))
    out_over05 = sorted(list(filter(over05, filtered_out)), key=lambda x: x['score'], reverse=True)
    out_below05 = sorted(list(filter(below05, filtered_out)), key=lambda x: x['distance'])
    out = [*out_over05, *out_below05]
    return {'count': len(out),'list': out}

@router.get("/nearby")
async def search_nearby(lat: float, lng: float, range: int = 10000,ctx = Depends(get_current_user), session: Session = Depends(get_db)):
    out = []
    user, _, _ = ctx
    
    if user.role != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Only user can use a search -> {user.role}")
    
    online_list = await online_ids()
    online_loc_lst = [await get_loc(x) for x in online_list]
    
    from haversine import haversine
    def filter_by_range(x):
        return haversine((lat,lng), (x['lat'], x['lng']), unit="m") <= range
    filterd_lst = list(filter(filter_by_range, online_loc_lst))
    
    ids: list[int] = [x['id'] for x in filterd_lst]
    q = session.query(SeniorAbilities).where(SeniorAbilities.id.in_(ids))
    rows = q.all()
    for r, usr in zip(rows, filterd_lst):
        data = {
            "id": usr['id'],
            "type": r.type,
            "career": r.career,
            "other_ability": r.other_ability,
            "vehicle": r.vehicle,
            "offsite_work": r.offsite_work,
            "distance": haversine((lat,lng), (usr['lat'], usr['lng']), unit="m")
        }
        out.append(data)
    out = sorted(out, key=lambda x: x['distance'])
    return {'count': len(out),'list': out}