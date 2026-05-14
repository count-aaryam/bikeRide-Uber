from app.db.session import engine, Base
from app.models.user import User
from app.models.ride import Ride

Base.metadata.create_all(bind=engine)

print("Tables created")