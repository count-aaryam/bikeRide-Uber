from fastapi import APIRouter, Depends, HTTPException
from app.services.user_service import (
    toggle_driver_status,
    get_available_drivers,
    update_driver_location
)
from app.schemas.user import UserOut, LocationUpdate
from app.dependencies.auth import get_current_user
from typing import List
from app.services.matching_service import get_nearby_drivers


router = APIRouter(prefix="/api/v1/driver")

@router.patch("/toggle-status")
def toggle_status(current_user=Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can toggle status")

    driver = toggle_driver_status(driver_id=current_user["user_id"])
    return {
        "message": f"You are now {'online' if driver.is_online else 'offline'}",
        "is_online": driver.is_online
    }

@router.get("/available", response_model=List[UserOut])
def available_drivers(current_user=Depends(get_current_user)):
    drivers = get_available_drivers()
    return drivers

@router.patch("/location")
def update_location(location: LocationUpdate, current_user=Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can update location")

    driver = update_driver_location(
        driver_id=current_user["user_id"],
        latitude=location.latitude,
        longitude=location.longitude
    )
    return {
        "message": "Location updated",
        "latitude": driver.latitude,
        "longitude": driver.longitude
    }

@router.get("/nearby")
async def nearby_drivers(
    lat: float,
    lng: float,
    radius: float = 5.0,
    current_user=Depends(get_current_user)
):
    """
    Rider calls this to see nearby available drivers
    before or after requesting a ride.
    """
    if current_user["role"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can search for nearby drivers")

    drivers = await get_nearby_drivers(
        pickup_lat=lat,
        pickup_lng=lng,
        radius_km=radius
    )

    return {
        "nearby_drivers": drivers,
        "count": len(drivers),
        "radius_km": radius
    }