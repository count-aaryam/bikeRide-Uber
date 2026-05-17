import re
from fastapi import HTTPException

def validate_email(email: str):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    if not re.match(pattern, email):
        raise HTTPException(
            status_code=422,
            detail="Invalid email format"
        )

def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(
            status_code=422,
            detail="Password must be at least 8 characters"
        )
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=422,
            detail="Password must contain at least one number"
        )

def validate_role(role: str):
    allowed = ["rider", "driver"]
    if role not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Role must be one of: {', '.join(allowed)}"
        )

def validate_phone(phone: str):
    if phone is None:
        return
    pattern = r'^\+?[0-9]{10,15}$'
    if not re.match(pattern, phone):
        raise HTTPException(
            status_code=422,
            detail="Invalid phone number format"
        )