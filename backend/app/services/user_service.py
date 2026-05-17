from sqlalchemy.orm import Session
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

def create_user(db: Session, name, email, password, role, phone=None):
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

async def toggle_driver_status(db: Session, driver_id: int):
    driver = db.query(User).filter(User.id == driver_id).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if driver.role != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can toggle status")

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

def get_available_drivers(db: Session):
    return db.query(User).filter(
        User.role == "driver",
        User.is_online == True
    ).all()

async def update_driver_location_service(db: Session, driver_id: int, latitude: float, longitude: float):
    driver = db.query(User).filter(User.id == driver_id).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if driver.role != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can update location")

    await update_driver_location(driver_id, latitude, longitude)

    driver.latitude = latitude
    driver.longitude = longitude
    db.commit()
    db.refresh(driver)
    return driver