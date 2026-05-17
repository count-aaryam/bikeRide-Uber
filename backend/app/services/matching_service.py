from app.services.redis_service import get_online_driver_ids, get_driver_location
from app.utils.geo import haversine

async def get_nearby_drivers(pickup_lat: float, pickup_lng: float, radius_km: float = 5.0) -> list:
    """
    Fetch all online drivers from Redis, get their cached
    locations, filter by radius, return sorted by distance.
    PostgreSQL is not touched — this is pure Redis + in-memory.
    """
    online_driver_ids = await get_online_driver_ids()

    nearby = []

    for driver_id in online_driver_ids:
        location = await get_driver_location(driver_id)

        # Skip drivers with no cached location
        if not location:
            continue

        distance = haversine(
            pickup_lat,
            pickup_lng,
            location["latitude"],
            location["longitude"]
        )

        if distance <= radius_km:
            nearby.append({
                "driver_id": driver_id,
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "distance_km": round(distance, 2),
                "last_updated": location["timestamp"]
            })

    # Sort closest first
    nearby.sort(key=lambda d: d["distance_km"])
    return nearby