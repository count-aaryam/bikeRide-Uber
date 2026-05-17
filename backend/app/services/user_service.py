from app.db.session import SessionLocal
from app.models.user import User
from app.models.ride import Ride
from app.core.security import hash_password
from app.services.redis_service import (
    set_driver_online,
    set_driver_offline,
    is_driver_online,
    update_driver_location
)
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

def create_user(name, email, password, role, phone=None):
    db = SessionLocal()
    try:
        user = User(
            name=name,
            email=email,
            phone=phone,
            password=hash_password(password),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    finally:
        db.close()

async def toggle_driver_status(driver_id: int):
    db = SessionLocal()
    try:
        driver = db.query(User).filter(User.id == driver_id).first()

        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        if driver.role != "driver":
            raise HTTPException(status_code=403, detail="Only drivers can toggle status")

        # Check for active ride before going offline
        active_ride = db.query(Ride).filter(
            Ride.driver_id == driver_id,
            Ride.status.in_(["accepted", "driver_arriving", "in_progress"])
        ).first()

        currently_online = await is_driver_online(driver_id)

        if active_ride and currently_online:
            raise HTTPException(
                status_code=400,
                detail="Cannot go offline while you have an active ride"
            )

        if currently_online:
            await set_driver_offline(driver_id)
            driver.is_online = False
        else:
            await set_driver_online(driver_id)
            driver.is_online = True

        db.commit()
        db.refresh(driver)
        return driver
    finally:
        db.close()

def get_available_drivers():
    db = SessionLocal()
    try:
        return db.query(User).filter(
            User.role == "driver",
            User.is_online == True
        ).all()
    finally:
        db.close()

async def update_driver_location_service(driver_id: int, latitude: float, longitude: float):
    db = SessionLocal()
    try:
        driver = db.query(User).filter(User.id == driver_id).first()

        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        if driver.role != "driver":
            raise HTTPException(status_code=403, detail="Only drivers can update location")

        # Fast write to Redis for real-time access
        await update_driver_location(driver_id, latitude, longitude)

        # Also persist to PostgreSQL for history
        driver.latitude = latitude
        driver.longitude = longitude
        db.commit()
        db.refresh(driver)
        return driver
    finally:
        db.close()