from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
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
from app.db.session import get_db
from app.utils.response import success_response
from app.services.matching_service import get_nearby_drivers
from typing import List

router = APIRouter(prefix="/api/v1")

@router.post("/rides")
@limiter.limit("10/minute")
async def request_ride(
    request: Request,
    ride: RideCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can request rides")

    new_ride = await create_ride(
        db=db,
        pickup=ride.pickup,
        dropoff=ride.dropoff,
        rider_id=current_user["user_id"]
    )

    if ride.pickup_lat and ride.pickup_lng:
        nearby = await get_nearby_drivers(ride.pickup_lat, ride.pickup_lng)
        target_driver_ids = [d["driver_id"] for d in nearby]
    else:
        target_driver_ids = get_online_driver_ids_from_db(db)

    await manager.broadcast_to_all_drivers({
        "event": RideEvents.NEW_RIDE_REQUESTED,
        "ride_id": new_ride.id,
        "pickup": new_ride.pickup,
        "dropoff": new_ride.dropoff
    }, target_driver_ids)

    return success_response(
        data={"ride_id": new_ride.id},
        message="Ride requested"
    )


@router.get("/rides/feed")
def ride_feed(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Drivers only")
    rides = get_available_rides(db)
    return success_response(
        data=[{
            "id": r.id,
            "pickup": r.pickup,
            "dropoff": r.dropoff,
            "status": r.status,
            "rider_id": r.rider_id
        } for r in rides],
        message="Available rides fetched"
    )


@router.patch("/rides/{ride_id}/accept")
async def accept_ride_endpoint(
    ride_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can accept rides")

    ride = await accept_ride(db, ride_id=ride_id, driver_id=current_user["user_id"])

    await manager.send_to_user(ride.rider_id, {
        "event": RideEvents.RIDE_ACCEPTED,
        "ride_id": ride.id,
        "driver_id": ride.driver_id,
        "status": ride.status
    })

    return success_response(
        data={"ride_id": ride.id, "status": ride.status},
        message="Ride accepted"
    )


@router.patch("/rides/{ride_id}/arriving")
async def driver_arriving_endpoint(
    ride_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can update arrival status")

    ride = await mark_driver_arriving(db, ride_id=ride_id, driver_id=current_user["user_id"])

    await manager.broadcast_to_ride_room(ride_id, {
        "event": RideEvents.DRIVER_ARRIVING,
        "ride_id": ride.id,
        "status": ride.status
    })

    return success_response(
        data={"ride_id": ride.id, "status": ride.status},
        message="Rider notified you are arriving"
    )


@router.get("/rides/{ride_id}/otp")
def get_otp(
    ride_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can view the OTP")
    otp = get_ride_otp(db, ride_id=ride_id, rider_id=current_user["user_id"])
    return success_response(data={"ride_id": ride_id, "otp": otp})


@router.patch("/rides/{ride_id}/start")
async def start_ride_endpoint(
    ride_id: int,
    body: RideOTPVerify,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can start rides")

    ride = await start_ride(db, ride_id=ride_id, driver_id=current_user["user_id"], otp=body.otp)

    await manager.broadcast_to_ride_room(ride_id, {
        "event": RideEvents.RIDE_STARTED,
        "ride_id": ride.id,
        "status": ride.status
    })

    return success_response(
        data={"ride_id": ride.id, "status": ride.status},
        message="Ride started"
    )


@router.patch("/rides/{ride_id}/complete")
async def complete_ride_endpoint(
    ride_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can complete rides")

    ride = await complete_ride(db, ride_id=ride_id, driver_id=current_user["user_id"])

    await manager.broadcast_to_ride_room(ride_id, {
        "event": RideEvents.RIDE_COMPLETED,
        "ride_id": ride.id,
        "status": ride.status
    })

    return success_response(
        data={"ride_id": ride.id, "status": ride.status},
        message="Ride completed"
    )


@router.patch("/rides/{ride_id}/cancel")
async def cancel_ride_endpoint(
    ride_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ride = await cancel_ride(
        db,
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

    return success_response(
        data={"ride_id": ride.id, "status": ride.status},
        message="Ride cancelled"
    )


@router.get("/rides/my-rides")
def rider_history(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "rider":
        raise HTTPException(status_code=403, detail="Only riders can view ride history")
    rides = get_rider_history(db, rider_id=current_user["user_id"])
    return success_response(
        data=[{
            "id": r.id,
            "pickup": r.pickup,
            "dropoff": r.dropoff,
            "status": r.status,
            "rider_id": r.rider_id,
            "driver_id": r.driver_id,
            "fare": r.fare,
            "distance_km": r.distance_km,
            "created_at": str(r.created_at) if r.created_at else None
        } for r in rides],
        message="Ride history fetched"
    )


@router.get("/rides/my-trips")
def driver_history(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can view trip history")
    rides = get_driver_history(db, driver_id=current_user["user_id"])
    return success_response(
        data=[{
            "id": r.id,
            "pickup": r.pickup,
            "dropoff": r.dropoff,
            "status": r.status,
            "rider_id": r.rider_id,
            "driver_id": r.driver_id,
            "fare": r.fare,
            "distance_km": r.distance_km,
            "created_at": str(r.created_at) if r.created_at else None
        } for r in rides],
        message="Trip history fetched"
    )