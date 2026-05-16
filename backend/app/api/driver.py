from fastapi import APIRouter, Depends, HTTPException
from app.services.user_service import (
    toggle_driver_status,
    get_available_drivers,
    update_driver_location
)
from app.schemas.user import UserOut, LocationUpdate
from app.dependencies.auth import get_current_user
from typing import List

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
@router.get("/available", response_model=List[UserOut])
def available_drivers(current_user=Depends(get_current_user)):
    # Only admin can see the full list of available drivers
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )
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