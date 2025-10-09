from fastapi import APIRouter, Depends, HTTPException, status

from fastapi.concurrency import run_in_threadpool
from numpy import sort
from sqlalchemy.orm import Session

from app.utils.file_upload import get_file_url

from ..utils.score import setScore

from ..services.user import getUser_by_ability_id, getUser_by_id

from ..database.redis import get_loc, get_locations_batch, online_ids

from ..database.models.senior_users import SeniorAbilities, SeniorProfiles, SeniorUsers

from ..utils.embedder import embed_query

from ..utils.deps import get_current_user, get_db
from ..utils.schemas import SearchOut, SearchPayload

router = APIRouter(prefix="/search", tags=["search"])

@router.get("")
async def Search(q: str, lat: float, lng: float, top_k: int = 20, radius: int = 10000, ctx = Depends(get_current_user), session: Session = Depends(get_db)):
    user, _, _ = ctx
    
    if user.role != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Only user can use a search -> {user.role}")
    
    online_list = await online_ids()
    stmt = session.query(SeniorUsers).where(SeniorUsers.id.in_(online_list))
    rows = stmt.all()
    
    qvec = embed_query(q)
    stmt = (
            session.query(
                SeniorAbilities, 
                1 - SeniorAbilities.embedding.cosine_distance(qvec).label("sim")
            )
            .where(SeniorAbilities.id.in_([x.ability_id for x in rows]))
            .order_by(SeniorAbilities.embedding.cosine_distance(qvec))
            .limit(top_k)
        )
    rows: SeniorAbilities = stmt.all()
    
    out = []
    for ability,sim in rows:
        user: SeniorUsers = ability.user
        profile: SeniorProfiles = user.profile
        location = await get_loc(user.id)
        
        if location is None:
            pass
        
        from haversine import haversine
        
        dist = haversine((lat, lng),(location['lat'], location['lng']), unit="m")
        
        score = setScore(sim, dist, 0.7, radius)
        data = {
            "id": user.id,
            "score": score,
            "name": profile.first_name + " " + profile.last_name,
            "type": ability.type,
            "phone": profile.phone,
            "work_experience": ability.work_experience,
            "other_ability": ability.other_ability,
            "vehicle": ability.vehicle,
            "offsite_work": ability.offsite_work,
            "chronic_diseases": profile.chronic_diseases,
            "distance": round(dist),
            "image_url": profile.image_url if profile.profile_image else None
        }
        out.append(data)
    def over05(x):
        return x['score'] >= 0.5
    def below05(x):
        return x['score'] < 0.5
    def range_filter(x):
        return x['distance'] <= radius
    filtered_out = list(filter(range_filter, out))
    out_over05 = sorted(list(filter(over05, filtered_out)), key=lambda x: x['score'], reverse=True)
    out_below05 = sorted(list(filter(below05, filtered_out)), key=lambda x: x['distance'])
    out = [*out_over05, *out_below05]
    return SearchOut(count=len(out), list=out)

@router.get("/nearby")
async def search_nearby(lat: float, lng: float, range: int = 10000,ctx = Depends(get_current_user), session: Session = Depends(get_db)):
    out = []
    user, _, _ = ctx
    
    if user.role != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Only user can use a search")
    
    online_list = await online_ids()
    online_loc_lst = [await get_loc(x) for x in online_list]
    
    q = session.query(SeniorUsers).where(SeniorUsers.id.in_(online_list))
    rows = q.all()
    
    from haversine import haversine
    def filter_by_range(x):
        return haversine((lat,lng), (x['lat'], x['lng']), unit="m") <= range
    filterd_lst = list(filter(filter_by_range, online_loc_lst))
    
    ids: list[str] = [x.ability_id for x in rows]
    q = session.query(SeniorAbilities).where(SeniorAbilities.id.in_(ids))
    rows: list[SeniorAbilities] = q.all()
    for ability, usr in zip(rows, filterd_lst):
        profile: SeniorProfiles = ability.user.profile
        profile_image = profile.profile_image
        if profile_image:
            profile.image_url = await run_in_threadpool(get_file_url, profile_image.file_path)
        data = {
            "id": usr['id'],
            "name": profile.first_name + " " + profile.last_name,
            "type": ability.type,
            "phone": profile.phone,
            "work_experience": ability.work_experience,
            "other_ability": ability.other_ability,
            "vehicle": ability.vehicle,
            "offsite_work": ability.offsite_work,
            "chronic_diseases": profile.chronic_diseases,
            "distance": round(haversine((lat,lng), (usr['lat'], usr['lng']), unit="m")),
            "image_url": profile.image_url if profile.profile_image else None
        }
        out.append(data)
    out = sorted(out, key=lambda x: x['distance'])
    return SearchOut(count=len(out), list=out)