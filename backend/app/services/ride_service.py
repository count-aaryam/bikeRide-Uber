from app.db.session import SessionLocal
from app.models.ride import Ride

def create_ride(pickup, dropoff, rider_id):
    db = SessionLocal()

    ride = Ride(
        pickup=pickup,
        dropoff=dropoff,
        rider_id=rider_id
    )

    db.add(ride)
    db.commit()
    db.refresh(ride)
    db.close()

    return ride