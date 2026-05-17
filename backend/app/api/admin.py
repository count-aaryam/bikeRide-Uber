from fastapi import APIRouter, Depends
from app.services.admin_service import (
    get_all_users,
    get_all_rides,
    get_active_rides,
    force_cancel_ride,
    delete_user,
    get_app_stats
)
from app.schemas.admin import UserAdminOut, RideAdminOut
from app.dependencies.auth import get_current_admin
from app.websocket.connection_manager import manager
from app.websocket.events import RideEvents
from typing import List

router = APIRouter(prefix="/api/v1/admin")

@router.get("/users", response_model=List[UserAdminOut])
def list_users(current_admin=Depends(get_current_admin)):
    return get_all_users()


@router.get("/rides", response_model=List[RideAdminOut])
def list_rides(current_admin=Depends(get_current_admin)):
    return get_all_rides()


@router.get("/rides/active", response_model=List[RideAdminOut])
def list_active_rides(current_admin=Depends(get_current_admin)):
    return get_active_rides()


@router.patch("/rides/{ride_id}/cancel")
async def admin_cancel_ride(ride_id: int, current_admin=Depends(get_current_admin)):
    ride = force_cancel_ride(ride_id=ride_id)

    # Notify both rider and driver
    await manager.broadcast_to_ride_room(ride_id, {
        "event": RideEvents.RIDE_CANCELLED,
        "ride_id": ride.id,
        "status": ride.status,
        "cancelled_by": "admin"
    })

    return {
        "message": f"Ride {ride_id} force cancelled by admin",
        "ride_id": ride.id,
        "status": ride.status
    }


@router.delete("/users/{user_id}")
def remove_user(user_id: int, current_admin=Depends(get_current_admin)):
    return delete_user(user_id=user_id)


@router.get("/stats")
def app_stats(current_admin=Depends(get_current_admin)):
    return get_app_stats()