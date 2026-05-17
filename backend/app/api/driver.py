from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.user_service import (
    toggle_driver_status,
    get_available_drivers,
    update_driver_location_service
)
from app.services.redis_service import get_driver_location
from app.services.matching_service import get_nearby_drivers
from app.schemas.user import UserOut, LocationUpdate
from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.utils.response import success_response
from typing import List

router = APIRouter(prefix="/api/v1/driver")

@router.patch("/toggle-status")
async def toggle_status(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can toggle status")

    driver = await toggle_driver_status(db, driver_id=current_user["user_id"])
    return success_response(
        data={"is_online": driver.is_online},
        message=f"You are now {'online' if driver.is_online else 'offline'}"
    )

@router.get("/available")
def available_drivers(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    drivers = get_available_drivers(db)
    return success_response(
        data=[{
            "id": d.id,
            "name": d.name,
            "email": d.email,
            "role": d.role,
            "is_online": d.is_online,
            "latitude": d.latitude,
            "longitude": d.longitude
        } for d in drivers],
        message="Available drivers fetched"
    )

@router.patch("/location")
async def update_location(
    location: LocationUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can update location")

    driver = await update_driver_location_service(
        db,
        driver_id=current_user["user_id"],
        latitude=location.latitude,
        longitude=location.longitude
    )
    return success_response(
        data={"latitude": driver.latitude, "longitude": driver.longitude},
        message="Location updated"
    )

@router.get("/location/{driver_id}")
async def get_location(driver_id: int, current_user=Depends(get_current_user)):
    location = await get_driver_location(driver_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not available")
    return success_response(data=location)

@router.get("/nearby")
async def nearby_drivers(
    lat: float,
    lng: float,
    radius: float = 5.0,
    current_user=Depends(get_current_user)
):
    if current_user["role"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can search for nearby drivers")

    drivers = await get_nearby_drivers(lat, lng, radius)
    return success_response(
        data={"nearby_drivers": drivers, "count": len(drivers), "radius_km": radius}
    )