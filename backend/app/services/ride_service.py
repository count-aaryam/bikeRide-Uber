from sqlalchemy.orm import Session
from app.models.ride import Ride
from app.models.user import User
from app.services.redis_service import (
    cache_ride_state,
    delete_ride_state
)
from fastapi import HTTPException
import random

def generate_otp() -> str:
    return str(random.randint(1000, 9999))

async def create_ride(db: Session, pickup, dropoff, rider_id):
    ride = Ride(pickup=pickup, dropoff=dropoff, rider_id=rider_id)
    db.add(ride)
    db.commit()
    db.refresh(ride)
    await cache_ride_state(ride.id, "requested", rider_id)
    return ride

def get_available_rides(db: Session):
    return db.query(Ride).filter(
        Ride.status == "requested",
        Ride.driver_id == None
    ).all()

def get_online_driver_ids_from_db(db: Session):
    drivers = db.query(User).filter(
        User.role == "driver",
        User.is_online == True
    ).all()
    return [d.id for d in drivers]

async def accept_ride(db: Session, ride_id: int, driver_id: int):
    ride = db.query(Ride).filter(
        Ride.id == ride_id
    ).with_for_update().first()

    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if ride.status != "requested" or ride.driver_id is not None:
        raise HTTPException(status_code=409, detail="Ride already accepted by another driver")

    ride.driver_id = driver_id
    ride.status = "accepted"
    ride.otp = generate_otp()

    db.commit()
    db.refresh(ride)
    await cache_ride_state(ride.id, "accepted", ride.rider_id, driver_id)
    return ride

async def mark_driver_arriving(db: Session, ride_id: int, driver_id: int):
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

def get_ride_otp(db: Session, ride_id: int, rider_id: int):
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

async def start_ride(db: Session, ride_id: int, driver_id: int, otp: str):
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

async def complete_ride(db: Session, ride_id: int, driver_id: int):
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
    await delete_ride_state(ride.id)
    return ride

async def cancel_ride(db: Session, ride_id: int, user_id: int, role: str):
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
    await delete_ride_state(ride.id)
    return ride

def get_rider_history(db: Session, rider_id: int):
    return db.query(Ride).filter(
        Ride.rider_id == rider_id
    ).order_by(Ride.id.desc()).all()

def get_driver_history(db: Session, driver_id: int):
    return db.query(Ride).filter(
        Ride.driver_id == driver_id
    ).order_by(Ride.id.desc()).all()