from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base

class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    rider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    pickup = Column(String, nullable=False)
    dropoff = Column(String, nullable=False)

    status = Column(String, default="requested")
    # requested → accepted → driver_arriving → in_progress → completed
    # requested → cancelled
    # accepted  → cancelled

    fare = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)
    otp = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())