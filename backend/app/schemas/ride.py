from pydantic import BaseModel

class RideCreate(BaseModel):
    pickup: str
    dropoff: str