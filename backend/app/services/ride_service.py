from app.db.session import SessionLocal
from app.models.ride import Ride
from app.models.user import User
from app.websocket.connection_manager import manager
from app.websocket.events import RideEvents
from app.services.redis_service import (
    cache_ride_state,
    delete_ride_state,
    get_online_driver_ids
)
from fastapi import HTTPException
import random

def generate_otp() -> str:
    return str(random.randint(1000, 9999))

async def create_ride(pickup, dropoff, rider_id):
    db = SessionLocal()
    try:
        ride = Ride(pickup=pickup, dropoff=dropoff, rider_id=rider_id)
        db.add(ride)
        db.commit()
        db.refresh(ride)
        # Cache initial ride state
        await cache_ride_state(ride.id, "requested", rider_id)
        return ride
    finally:
        db.close()

def get_available_rides():
    db = SessionLocal()
    try:
        return db.query(Ride).filter(
            Ride.status == "requested",
            Ride.driver_id == None
        ).all()
    finally:
        db.close()

def get_online_driver_ids_from_db():
    db = SessionLocal()
    try:
        drivers = db.query(User).filter(
            User.role == "driver",
            User.is_online == True
        ).all()
        return [d.id for d in drivers]
    finally:
        db.close()

async def accept_ride(ride_id: int, driver_id: int):
    db = SessionLocal()
    try:
        ride = db.query(Ride).filter(Ride.id == ride_id).with_for_update().first()

        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        if ride.status != "requested" or ride.driver_id is not None:
            raise HTTPException(status_code=409, detail="Ride already accepted by another driver")

        ride.driver_id = driver_id
        ride.status = "accepted"
        ride.otp = generate_otp()

        db.commit()
        db.refresh(ride)

        # Update Redis cache
        await cache_ride_state(ride.id, "accepted", ride.rider_id, driver_id)
        return ride
    finally:
        db.close()

async def mark_driver_arriving(ride_id: int, driver_id: int):
    db = SessionLocal()
    try:
        ride = db.query(Ride).filter(Ride.id == ride_id).first()

        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        if ride.driver_id != driver_id:
            raise HTTPException(status_code=403, detail="You are not assigned to this ride")
        if ride.status != "accepted":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot mark arriving from status '{ride.status}'"
            )

        ride.status = "driver_arriving"
        db.commit()
        db.refresh(ride)

        await cache_ride_state(ride.id, "driver_arriving", ride.rider_id, driver_id)
        return ride
    finally:
        db.close()

def get_ride_otp(ride_id: int, rider_id: int):
    db = SessionLocal()
    try:
        ride = db.query(Ride).filter(Ride.id == ride_id).first()

        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        if ride.rider_id != rider_id:
            raise HTTPException(status_code=403, detail="This is not your ride")
        if ride.status not in ["accepted", "driver_arriving"]:
            raise HTTPException(
                status_code=400,
                detail="OTP only available once ride is accepted"
            )
        return ride.otp
    finally:
        db.close()

async def start_ride(ride_id: int, driver_id: int, otp: str):
    db = SessionLocal()
    try:
        ride = db.query(Ride).filter(Ride.id == ride_id).first()

        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        if ride.driver_id != driver_id:
            raise HTTPException(status_code=403, detail="You are not assigned to this ride")
        if ride.status != "driver_arriving":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot start ride from status '{ride.status}'"
            )
        if ride.otp != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        ride.status = "in_progress"
        ride.otp = None
        db.commit()
        db.refresh(ride)

        await cache_ride_state(ride.id, "in_progress", ride.rider_id, driver_id)
        return ride
    finally:
        db.close()

async def complete_ride(ride_id: int, driver_id: int):
    db = SessionLocal()
    try:
        ride = db.query(Ride).filter(Ride.id == ride_id).first()

        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        if ride.driver_id != driver_id:
            raise HTTPException(status_code=403, detail="You are not assigned to this ride")
        if ride.status != "in_progress":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot complete ride from status '{ride.status}'"
            )

        ride.status = "completed"
        db.commit()
        db.refresh(ride)

        # Remove from cache — ride is done
        await delete_ride_state(ride.id)
        return ride
    finally:
        db.close()

async def cancel_ride(ride_id: int, user_id: int, role: str):
    db = SessionLocal()
    try:
        ride = db.query(Ride).filter(Ride.id == ride_id).first()

        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")

        if role == "rider":
            if ride.rider_id != user_id:
                raise HTTPException(status_code=403, detail="You can only cancel your own ride")
            if ride.status not in ["requested"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Rider cannot cancel a ride with status '{ride.status}'"
                )

        elif role == "driver":
            if ride.driver_id != user_id:
                raise HTTPException(status_code=403, detail="You are not assigned to this ride")
            if ride.status not in ["accepted", "driver_arriving"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Driver cannot cancel a ride with status '{ride.status}'"
                )

        ride.status = "cancelled"
        ride.otp = None
        db.commit()
        db.refresh(ride)

        # Remove from cache
        await delete_ride_state(ride.id)
        return ride
    finally:
        db.close()

def get_rider_history(rider_id: int):
    db = SessionLocal()
    try:
        return db.query(Ride).filter(
            Ride.rider_id == rider_id
        ).order_by(Ride.id.desc()).all()
    finally:
        db.close()

def get_driver_history(driver_id: int):
    db = SessionLocal()
    try:
        return db.query(Ride).filter(
            Ride.driver_id == driver_id
        ).order_by(Ride.id.desc()).all()
    finally:
        db.close()