from fastapi import APIRouter, Depends
from app.schemas.ride import RideCreate
from app.services.ride_service import create_ride
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/v1")

@router.post("/rides")
def request_ride(ride: RideCreate, current_user=Depends(get_current_user)):

    if current_user["role"] != "rider":
        return {"error": "Only riders can request rides"}

    new_ride = create_ride(
        pickup=ride.pickup,
        dropoff=ride.dropoff,
        rider_id=current_user["user_id"]
    )

    return {
        "message": "Ride requested",
        "ride_id": new_ride.id
    }