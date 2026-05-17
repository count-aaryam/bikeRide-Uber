from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

class RideCreate(BaseModel):
    pickup: str
    dropoff: str
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None

    @field_validator("pickup", "dropoff")
    def location_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Location cannot be empty")
        if len(v.strip()) < 3:
            raise ValueError("Location must be at least 3 characters")
        return v.strip()

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

    @field_validator("otp")
    def otp_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError("OTP cannot be empty")
        if not v.strip().isdigit():
            raise ValueError("OTP must be numeric")
        if len(v.strip()) != 4:
            raise ValueError("OTP must be 4 digits")
        return v.strip()