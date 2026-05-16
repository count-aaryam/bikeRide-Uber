from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password
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

def toggle_driver_status(driver_id: int):
    db = SessionLocal()
    try:
        driver = db.query(User).filter(User.id == driver_id).first()

        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        if driver.role != "driver":
            raise HTTPException(status_code=403, detail="Only drivers can toggle status")

        # Check if driver has an active ride
        from app.models.ride import Ride
        active_ride = db.query(Ride).filter(
            Ride.driver_id == driver_id,
            Ride.status.in_(["accepted", "driver_arriving", "in_progress"])
        ).first()

        if active_ride and driver.is_online:
            raise HTTPException(
                status_code=400,
                detail="Cannot go offline while you have an active ride"
            )

        # Toggle
        driver.is_online = not driver.is_online
        db.commit()
        db.refresh(driver)
        return driver
    finally:
        db.close()

def get_available_drivers():
    db = SessionLocal()
    try:
        drivers = db.query(User).filter(
            User.role == "driver",
            User.is_online == True
        ).all()
        return drivers
    finally:
        db.close()

def update_driver_location(driver_id: int, latitude: float, longitude: float):
    db = SessionLocal()
    try:
        driver = db.query(User).filter(User.id == driver_id).first()

        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        if driver.role != "driver":
            raise HTTPException(status_code=403, detail="Only drivers can update location")

        driver.latitude = latitude
        driver.longitude = longitude
        db.commit()
        db.refresh(driver)
        return driver
    finally:
        db.close()