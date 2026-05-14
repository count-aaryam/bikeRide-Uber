from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.session import Base

class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)

    pickup = Column(String)
    dropoff = Column(String)

    status = Column(String, default="requested")

    rider_id = Column(Integer, ForeignKey("users.id"))
    driver_id = Column(Integer, nullable=True)