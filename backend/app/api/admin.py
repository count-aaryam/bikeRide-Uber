from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.admin_service import (
    get_all_users, get_all_rides, get_active_rides,
    force_cancel_ride, delete_user, get_app_stats
)
from app.schemas.admin import UserAdminOut, RideAdminOut
from app.dependencies.auth import get_current_admin
from app.websocket.connection_manager import manager
from app.websocket.events import RideEvents
from app.db.session import get_db
from app.utils.response import success_response
from typing import List
from app.utils.pagination import get_pagination, paginate_response, PaginationParams

router = APIRouter(prefix="/api/v1/admin")

@router.get("/users")
def list_users(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination)
):
    users, total = get_all_users(db, offset=pagination.offset, limit=pagination.limit)
    return success_response(
        data=paginate_response(
            data=[{
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "phone": u.phone,
                "role": u.role,
                "is_online": u.is_online,
                "created_at": str(u.created_at) if u.created_at else None
            } for u in users],
            total=total,
            pagination=pagination
        ),
        message="Users fetched"
    )


@router.get("/rides")
def list_rides(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination)
):
    rides, total = get_all_rides(db, offset=pagination.offset, limit=pagination.limit)
    return success_response(
        data=paginate_response(
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
            total=total,
            pagination=pagination
        ),
        message="All rides fetched"
    )


@router.get("/rides/active")
def list_active_rides(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination)
):
    rides, total = get_active_rides(db, offset=pagination.offset, limit=pagination.limit)
    return success_response(
        data=paginate_response(
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
            total=total,
            pagination=pagination
        ),
        message="Active rides fetched"
    )

@router.patch("/rides/{ride_id}/cancel")
async def admin_cancel_ride(
    ride_id: int,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    ride = force_cancel_ride(db, ride_id=ride_id)

    await manager.broadcast_to_ride_room(ride_id, {
        "event": RideEvents.RIDE_CANCELLED,
        "ride_id": ride.id,
        "status": ride.status,
        "cancelled_by": "admin"
    })

    return success_response(
        data={"ride_id": ride.id, "status": ride.status},
        message=f"Ride {ride_id} force cancelled by admin"
    )

@router.delete("/users/{user_id}")
def remove_user(
    user_id: int,
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    result = delete_user(db, user_id=user_id)
    return success_response(message=result["message"])

@router.get("/stats")
def app_stats(
    current_admin=Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return success_response(data=get_app_stats(db))