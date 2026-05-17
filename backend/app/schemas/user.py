from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    phone: Optional[str] = None

    @field_validator("name")
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("email")
    def email_must_be_valid(cls, v):
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        if not re.match(pattern, v.lower()):
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("password")
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("role")
    def role_must_be_valid(cls, v):
        allowed = ["rider", "driver"]
        if v not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(allowed)}")
        return v

    @field_validator("phone")
    def phone_must_be_valid(cls, v):
        if v is None:
            return v
        import re
        pattern = r'^\+?[0-9]{10,15}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid phone number format")
        return v

class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def email_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Email cannot be empty")
        return v.lower().strip()

    @field_validator("password")
    def password_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Password cannot be empty")
        return v

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_online: bool
    latitude: Optional[float]
    longitude: Optional[float]

    class Config:
        from_attributes = True

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float

    @field_validator("latitude")
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v