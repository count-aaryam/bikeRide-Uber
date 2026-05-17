from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserAdminOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    role: str
    is_online: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

class RideAdminOut(BaseModel):
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