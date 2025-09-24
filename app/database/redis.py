from __future__ import annotations
from typing import Dict, List, Optional
from redis.asyncio import Redis

from ..utils.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, PRESENCE_TTL_SECONDS

import json

_redis: Redis | None = None

def get_redis() -> Redis:
    global _redis
    if _redis is None:
        host = REDIS_HOST
        port = REDIS_PORT
        db = REDIS_DB
        username = None
        password = REDIS_PASSWORD

        _redis = Redis(
            host=host,
            port=port,
            db=db,
            username=username,
            password=password,
            decode_responses=True,  # ทำให้ได้ str แทน bytes
        )
    return _redis

# -------- Key design --------
def _presence_key(pid: str) -> str:
    return f"senior:{pid}:presence"

def _loc_key(pid: str) -> str:
    return f"senior:{pid}:loc"

async def set_presence(provider_id: str, ttl: int) -> None:
    """
    เก็บสถานะออนไลน์ (presence) ไว้ใน Redis พร้อม TTL
    """
    r = get_redis()
    await r.setex(_presence_key(provider_id), ttl, "1")

async def set_presence_and_loc(
    provider_id: str,
    lat: float,
    lng: float,
    ttl: int,
) -> None:
    """
    เก็บสถานะออนไลน์ + พิกัดสดไว้ใน Redis พร้อม TTL
    ใช้ pipeline ลด RTT; ไม่เก็บถาวร (privacy-first); payload ที่เก็บ: {"id", "lat", "lng"}
    """
    
    if lat is None or lng is None:
        raise ValueError("lat and lng are required")
    
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ValueError("Invalid lat/lng")
    
    payload = {"id": provider_id, "lat": float(lat), "lng": float(lng)}
    
    await set_presence(provider_id, ttl)
    
    r = get_redis()
    pipe = r.pipeline()
    await pipe.setex(_loc_key(provider_id), ttl, json.dumps(payload))
    await pipe.execute()    
    
    
    
async def online_ids() -> List[int]:
    """
    คืนรายการ provider_id ที่ยังออนไลน์ (presence key ยังไม่หมดอายุ)
    ใช้ SCAN แทน KEYS สำหรับโปรดักชัน
    """
    r = get_redis()
    out: List[int] = []
    async for key in r.scan_iter(match="senior:*:presence", count=500):
        try:
            out.append(int(key.split(":")[1]))
        except Exception:
            continue
    return out

async def get_loc(pid: int) -> Optional[Dict]:
    """
    ดึงตำแหน่งล่าสุดของ provider ตาม pid
    คืนค่าเป็น {"id": pid, "lat": float, "lng": float} หรือ None ถ้าไม่มีข้อมูล/หมดอายุ
    """
    r = get_redis()
    raw = await r.get(_loc_key(pid))
    if not raw:
        return None
    try:
        obj = json.loads(raw)
        # เติม id หาก payload เดิมไม่มี (เผื่อ backward compatibility)
        if "id" not in obj:
            obj["id"] = int(pid)
        # แปลงชนิดให้ชัดเจน
        obj["id"] = int(obj["id"])
        obj["lat"] = float(obj["lat"])
        obj["lng"] = float(obj["lng"])
        return obj
    except Exception:
        return None

async def get_locations_batch(pids: List[int]) -> Dict[int, Dict]:
    """
    ดึงพิกัดของหลาย provider แบบ batch (pipeline) เพื่อประสิทธิภาพ
    """
    if not pids:
        return {}
    r = get_redis()
    pipe = r.pipeline()
    res: Dict[int, Dict] = {}
    for pid in pids:
        pipe.get(_loc_key(pid))
    vals = await pipe.execute()    
    for pid, raw in zip(pids, vals):
        if raw:
            try:
                res[pid] = json.loads(raw)
            except Exception:
                continue
    return res