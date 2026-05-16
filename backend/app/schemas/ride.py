from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RideCreate(BaseModel):
    pickup: str
    dropoff: str

class RideOut(BaseModel):
    id: int
    pickup: str
    dropoff: str
    status: str
    rider_id: int

    class Config:
        from_attributes = True

class RideHistoryOut(BaseModel):
    id: int
    pickup: str
    dropoff: str
    status: str
    rider_id: int
    driver_id: Optional[int]
    fare: Optional[float]
    distance_km: Optional[float]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

class RideOTPVerify(BaseModel):
    otp: str