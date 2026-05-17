import json
import time
from app.core.redis import get_redis


# ========================
# DRIVER ONLINE TRACKING
# ========================

async def set_driver_online(driver_id: int):
    """TTL 1 hour — auto expires if driver disconnects
    without explicitly going offline."""
    redis = await get_redis()
    await redis.set(f"driver:{driver_id}:online", "1", ex=3600)
    await redis.sadd("online_drivers", driver_id)

async def set_driver_offline(driver_id: int):
    redis = await get_redis()
    await redis.delete(f"driver:{driver_id}:online")
    await redis.srem("online_drivers", driver_id)

async def is_driver_online(driver_id: int) -> bool:
    redis = await get_redis()
    return await redis.exists(f"driver:{driver_id}:online") == 1

async def get_online_driver_ids() -> list:
    redis = await get_redis()
    members = await redis.smembers("online_drivers")
    return [int(m) for m in members]


# ========================
# DRIVER LOCATION
# ========================

async def update_driver_location(driver_id: int, latitude: float, longitude: float):
    """TTL 5 mins — stale location auto-expires if driver
    stops sending updates."""
    redis = await get_redis()
    location_data = json.dumps({
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": time.time()
    })
    await redis.set(f"driver:{driver_id}:location", location_data, ex=300)

async def get_driver_location(driver_id: int) -> dict:
    redis = await get_redis()
    data = await redis.get(f"driver:{driver_id}:location")
    return json.loads(data) if data else None


# ========================
# RIDE STATE CACHE
# ========================

async def cache_ride_state(ride_id: int, status: str, rider_id: int, driver_id: int = None):
    """PostgreSQL is source of truth — Redis just speeds up reads.
    TTL 24 hours."""
    redis = await get_redis()
    state = json.dumps({
        "status": status,
        "rider_id": rider_id,
        "driver_id": driver_id
    })
    await redis.set(f"ride:{ride_id}:state", state, ex=86400)

async def get_ride_state(ride_id: int) -> dict:
    redis = await get_redis()
    data = await redis.get(f"ride:{ride_id}:state")
    return json.loads(data) if data else None

async def delete_ride_state(ride_id: int):
    redis = await get_redis()
    await redis.delete(f"ride:{ride_id}:state")


# ========================
# JWT BLACKLIST
# ========================

async def blacklist_token(token: str, expires_in: int = 3600):
    """TTL matches token expiry so blacklist self-cleans."""
    redis = await get_redis()
    await redis.set(f"blacklist:{token}", "1", ex=expires_in)

async def is_token_blacklisted(token: str) -> bool:
    redis = await get_redis()
    return await redis.exists(f"blacklist:{token}") == 1


# ========================
# BACKGROUND CLEANUP
# ========================

async def cleanup_stale_drivers():
    """Remove drivers from online set if their TTL has expired."""
    redis = await get_redis()
    driver_ids = await redis.smembers("online_drivers")
    for driver_id in driver_ids:
        is_online = await redis.exists(f"driver:{driver_id}:online")
        if not is_online:
            await redis.srem("online_drivers", driver_id)
            print(f"Cleaned up stale driver {driver_id}")