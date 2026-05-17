from sqlalchemy.orm import Session
from app.models.user import User
from app.models.ride import Ride
from fastapi import HTTPException

def get_all_users(db: Session):
    return db.query(User).order_by(User.id.desc()).all()

def get_all_rides(db: Session):
    return db.query(Ride).order_by(Ride.id.desc()).all()

def get_active_rides(db: Session):
    return db.query(Ride).filter(
        Ride.status.in_(["requested", "accepted", "driver_arriving", "in_progress"])
    ).order_by(Ride.id.desc()).all()

def force_cancel_ride(db: Session, ride_id: int):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()

    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if ride.status in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel a ride with status '{ride.status}'"
        )

    ride.status = "cancelled"
    ride.otp = None
    db.commit()
    db.refresh(ride)
    return ride

def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete an admin user")

    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted"}

def get_app_stats(db: Session):
    total_users    = db.query(User).count()
    total_riders   = db.query(User).filter(User.role == "rider").count()
    total_drivers  = db.query(User).filter(User.role == "driver").count()
    online_drivers = db.query(User).filter(
        User.role == "driver",
        User.is_online == True
    ).count()
    total_rides     = db.query(Ride).count()
    active_rides    = db.query(Ride).filter(
        Ride.status.in_(["requested", "accepted", "driver_arriving", "in_progress"])
    ).count()
    completed_rides = db.query(Ride).filter(Ride.status == "completed").count()
    cancelled_rides = db.query(Ride).filter(Ride.status == "cancelled").count()

    return {
        "users": {
            "total": total_users,
            "riders": total_riders,
            "drivers": total_drivers,
            "online_drivers": online_drivers
        },
        "rides": {
            "total": total_rides,
            "active": active_rides,
            "completed": completed_rides,
            "cancelled": cancelled_rides
        }
    }