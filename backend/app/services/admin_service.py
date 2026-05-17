from app.db.session import SessionLocal
from app.models.user import User
from app.models.ride import Ride
from fastapi import HTTPException

def get_all_users():
    db = SessionLocal()
    try:
        return db.query(User).order_by(User.id.desc()).all()
    finally:
        db.close()

def get_all_rides():
    db = SessionLocal()
    try:
        return db.query(Ride).order_by(Ride.id.desc()).all()
    finally:
        db.close()

def get_active_rides():
    db = SessionLocal()
    try:
        return db.query(Ride).filter(
            Ride.status.in_(["requested", "accepted", "driver_arriving", "in_progress"])
        ).order_by(Ride.id.desc()).all()
    finally:
        db.close()

def force_cancel_ride(ride_id: int):
    db = SessionLocal()
    try:
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
    finally:
        db.close()

def delete_user(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.role == "admin":
            raise HTTPException(status_code=400, detail="Cannot delete an admin user")

        db.delete(user)
        db.commit()
        return {"message": f"User {user_id} deleted"}
    finally:
        db.close()

def get_app_stats():
    db = SessionLocal()
    try:
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
    finally:
        db.close()