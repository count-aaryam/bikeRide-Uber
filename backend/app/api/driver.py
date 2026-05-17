# FastAPI utilities:
# APIRouter -> groups related routes together
# Depends -> dependency injection system
# HTTPException -> used to throw API errors with status codes
from fastapi import APIRouter, Depends, HTTPException

# SQLAlchemy database session object.
# Session is the bridge between Python code and the database.
from sqlalchemy.orm import Session


# Importing business logic functions from service layer.
# Keeping logic outside routes is good architecture practice.
from app.services.user_service import (
    toggle_driver_status,          # Handles online/offline toggle logic
    get_available_drivers,         # Fetches all available drivers
    update_driver_location_service # Updates driver coordinates
)

# Redis-based location retrieval service.
# Redis is often used for realtime GPS/location systems because it is extremely fast.
from app.services.redis_service import get_driver_location

# Matching logic service.
# Likely contains geospatial search logic for finding nearby drivers.
from app.services.matching_service import get_nearby_drivers

# Pydantic schemas.
# Used for request validation and response typing.
from app.schemas.user import UserOut, LocationUpdate

# Authentication dependency.
# This probably validates JWT token and returns current logged-in user.
from app.dependencies.auth import get_current_user

# Database dependency function.
# Creates and provides database session to routes.
from app.db.session import get_db

# Standardized API response formatter.
# Helps maintain consistent response structure across the backend.
from app.utils.response import success_response

# Typing utility for type hints.
from typing import List


# Create router object.
# All endpoints inside this router will start with:
# /api/v1/driver
router = APIRouter(prefix="/api/v1/driver")


# ============================================================
# TOGGLE DRIVER ONLINE/OFFLINE STATUS
# ============================================================

# PATCH is used because we are partially updating driver data.
@router.patch("/toggle-status")
async def toggle_status(

    # Inject authenticated user automatically.
    # Example returned object:
    # {
    #   "user_id": 1,
    #   "role": "driver"
    # }
    current_user=Depends(get_current_user),

    # Inject database session automatically.
    db: Session = Depends(get_db)
):

    # Security check:
    # Only drivers are allowed to toggle status.
    if current_user["role"] != "driver":
        raise HTTPException(
            status_code=403,
            detail="Only drivers can toggle status"
        )

    # Call service function to toggle online/offline state.
    # Likely flips:
    # True -> False
    # False -> True
    driver = await toggle_driver_status(
        db,
        driver_id=current_user["user_id"]
    )

    # Return formatted success response.
    return success_response(
        data={
            "is_online": driver.is_online
        },

        # Dynamic message based on driver's new status.
        message=f"You are now {'online' if driver.is_online else 'offline'}"
    )


# ============================================================
# GET ALL AVAILABLE DRIVERS
# ============================================================

@router.get("/available")
def available_drivers(

    # User authentication required.
    current_user=Depends(get_current_user),

    # Database session injection.
    db: Session = Depends(get_db)
):

    # Fetch all available/online drivers from database.
    drivers = get_available_drivers(db)

    # Convert SQLAlchemy model objects into JSON serializable dictionaries.
    return success_response(
        data=[
            {
                "id": d.id,
                "name": d.name,
                "email": d.email,
                "role": d.role,
                "is_online": d.is_online,
                "latitude": d.latitude,
                "longitude": d.longitude
            }

            # Loop through every driver object.
            for d in drivers
        ],

        message="Available drivers fetched"
    )


# ============================================================
# UPDATE DRIVER LOCATION
# ============================================================

@router.patch("/location")
async def update_location(

    # Request body validation using Pydantic schema.
    # Expected JSON:
    # {
    #   "latitude": 18.52,
    #   "longitude": 73.85
    # }
    location: LocationUpdate,

    # Authenticated user injection.
    current_user=Depends(get_current_user),

    # Database session injection.
    db: Session = Depends(get_db)
):

    # Only drivers can update live GPS coordinates.
    if current_user["role"] != "driver":
        raise HTTPException(
            status_code=403,
            detail="Only drivers can update location"
        )

    # Update driver's location using service layer.
    # This may:
    # 1. Update database
    # 2. Update Redis cache
    # 3. Update geospatial index
    driver = await update_driver_location_service(
        db,

        # Logged-in driver's ID
        driver_id=current_user["user_id"],

        # GPS coordinates from request body
        latitude=location.latitude,
        longitude=location.longitude
    )

    # Return updated coordinates.
    return success_response(
        data={
            "latitude": driver.latitude,
            "longitude": driver.longitude
        },

        message="Location updated"
    )


# ============================================================
# GET SPECIFIC DRIVER LOCATION
# ============================================================

# Path parameter:
# Example:
# /location/5
# Here driver_id = 5
@router.get("/location/{driver_id}")
async def get_location(

    # FastAPI automatically converts URL parameter to int.
    driver_id: int,

    # User authentication dependency.
    current_user=Depends(get_current_user)
):

    # Fetch realtime driver location from Redis.
    location = await get_driver_location(driver_id)

    # If no location exists in cache/database.
    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not available"
        )

    # Return driver location.
    return success_response(data=location)


# ============================================================
# FIND NEARBY DRIVERS
# ============================================================

@router.get("/nearby")
async def nearby_drivers(

    # Latitude from query parameter.
    # Example:
    # /nearby?lat=18.5
    lat: float,

    # Longitude from query parameter.
    lng: float,

    # Search radius in kilometers.
    # Default = 5 km
    radius: float = 5.0,

    # Authenticated user dependency.
    current_user=Depends(get_current_user)
):

    # Only riders can search for nearby drivers.
    if current_user["role"] != "rider":
        raise HTTPException(
            status_code=403,
            detail="Only riders can search for nearby drivers"
        )

    # Find nearby drivers using matching service.
    #
    # Internally this may use:
    # - Haversine formula
    # - Redis GEOSEARCH
    # - PostGIS spatial queries
    # - KD-tree spatial indexing
    #
    # Goal:
    # Find drivers within given radius.
    drivers = await get_nearby_drivers(
        lat,
        lng,
        radius
    )

    # Return nearby driver data.
    return success_response(
        data={
            "nearby_drivers": drivers,

            # Total nearby drivers found
            "count": len(drivers),

            # Radius used for search
            "radius_km": radius
        },

        message="Nearby drivers fetched"
    )
