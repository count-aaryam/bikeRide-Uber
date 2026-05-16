from pydantic import BaseModel
from typing import Optional

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

class RideOTPVerify(BaseModel):
    otp: str