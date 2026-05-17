from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas.ride import RideCreate, RideOut, RideOTPVerify, RideHistoryOut
from app.services.ride_service import (
    create_ride, get_available_rides, accept_ride,
    mark_driver_arriving, get_ride_otp, start_ride,
    complete_ride, cancel_ride, get_rider_history,
    get_driver_history, get_online_driver_ids_from_db
)
from app.websocket.connection_manager import manager
from app.websocket.events import RideEvents
from app.dependencies.auth import get_current_user
from app.core.limiter import limiter
from typing import List
from app.services.matching_service import get_nearby_drivers



router = APIRouter(prefix="/api/v1")

@router.post("/rides")
@limiter.limit("10/minute")
async def request_ride(request: Request, ride: RideCreate, current_user=Depends(get_current_user)):
    if current_user["role"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can request rides")

    new_ride = await create_ride(
        pickup=ride.pickup,
        dropoff=ride.dropoff,
        rider_id=current_user["user_id"]
    )

    # Use nearby filtering if coordinates provided
    # Otherwise fall back to all online drivers
    if ride.pickup_lat and ride.pickup_lng:
        nearby = await get_nearby_drivers(
            pickup_lat=ride.pickup_lat,
            pickup_lng=ride.pickup_lng,
            radius_km=5.0
        )
        target_driver_ids = [d["driver_id"] for d in nearby]
    else:
        target_driver_ids = get_online_driver_ids_from_db()

    await manager.broadcast_to_all_drivers({
        "event": RideEvents.NEW_RIDE_REQUESTED,
        "ride_id": new_ride.id,
        "pickup": new_ride.pickup,
        "dropoff": new_ride.dropoff
    }, target_driver_ids)

    return {"message": "Ride requested", "ride_id": new_ride.id}


@router.get("/rides/feed", response_model=List[RideOut])
def ride_feed(current_user=Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Drivers only")
    return get_available_rides()


@router.patch("/rides/{ride_id}/accept")
async def accept_ride_endpoint(ride_id: int, current_user=Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can accept rides")

    ride = await accept_ride(ride_id=ride_id, driver_id=current_user["user_id"])

    await manager.send_to_user(ride.rider_id, {
        "event": RideEvents.RIDE_ACCEPTED,
        "ride_id": ride.id,
        "driver_id": ride.driver_id,
        "status": ride.status
    })

    return {"message": "Ride accepted", "ride_id": ride.id, "status": ride.status}


@router.patch("/rides/{ride_id}/arriving")
async def driver_arriving_endpoint(ride_id: int, current_user=Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can update arrival status")

    ride = await mark_driver_arriving(ride_id=ride_id, driver_id=current_user["user_id"])

    await manager.broadcast_to_ride_room(ride_id, {
        "event": RideEvents.DRIVER_ARRIVING,
        "ride_id": ride.id,
        "status": ride.status
    })

    return {
        "message": "Rider will be notified you are arriving",
        "ride_id": ride.id,
        "status": ride.status
    }


@router.get("/rides/{ride_id}/otp")
def get_otp(ride_id: int, current_user=Depends(get_current_user)):
    if current_user["role"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can view the OTP")
    otp = get_ride_otp(ride_id=ride_id, rider_id=current_user["user_id"])
    return {"ride_id": ride_id, "otp": otp}


@router.patch("/rides/{ride_id}/start")
async def start_ride_endpoint(ride_id: int, body: RideOTPVerify, current_user=Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can start rides")

    ride = await start_ride(
        ride_id=ride_id,
        driver_id=current_user["user_id"],
        otp=body.otp
    )

    await manager.broadcast_to_ride_room(ride_id, {
        "event": RideEvents.RIDE_STARTED,
        "ride_id": ride.id,
        "status": ride.status
    })

    return {"message": "Ride started", "ride_id": ride.id, "status": ride.status}


@router.patch("/rides/{ride_id}/complete")
async def complete_ride_endpoint(ride_id: int, current_user=Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can complete rides")

    ride = await complete_ride(ride_id=ride_id, driver_id=current_user["user_id"])

    await manager.broadcast_to_ride_room(ride_id, {
        "event": RideEvents.RIDE_COMPLETED,
        "ride_id": ride.id,
        "status": ride.status
    })

    return {"message": "Ride completed", "ride_id": ride.id, "status": ride.status}


@router.patch("/rides/{ride_id}/cancel")
async def cancel_ride_endpoint(ride_id: int, current_user=Depends(get_current_user)):
    ride = await cancel_ride(
        ride_id=ride_id,
        user_id=current_user["user_id"],
        role=current_user["role"]
    )

    await manager.broadcast_to_ride_room(ride_id, {
        "event": RideEvents.RIDE_CANCELLED,
        "ride_id": ride.id,
        "status": ride.status,
        "cancelled_by": current_user["role"]
    })

    return {"message": "Ride cancelled", "ride_id": ride.id, "status": ride.status}


@router.get("/rides/my-rides", response_model=List[RideHistoryOut])
def rider_history(current_user=Depends(get_current_user)):
    if current_user["role"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can view ride history")
    return get_rider_history(rider_id=current_user["user_id"])


@router.get("/rides/my-trips", response_model=List[RideHistoryOut])
def driver_history(current_user=Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can view trip history")
    return get_driver_history(driver_id=current_user["user_id"])