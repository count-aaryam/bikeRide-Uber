from fastapi import APIRouter, Depends, Request
from app.schemas.user import UserCreate
from app.services.user_service import create_user
from app.dependencies.auth import get_current_user
from app.core.limiter import limiter

router = APIRouter(prefix="/api/v1")

@router.post("/users")
@limiter.limit("3/minute")
def signup(request: Request, user: UserCreate):
    created_user = create_user(
        name=user.name,
        email=user.email,
        password=user.password,
        role=user.role,
        phone=user.phone
    )
    return {
        "message": "User created",
        "id": created_user.id
    }

@router.get("/profile")
def profile(current_user=Depends(get_current_user)):
    return {
        "message": "Protected route accessed",
        "user": current_user
    }

@router.get("/driver-only")
def driver_route(current_user=Depends(get_current_user)):
    if current_user["role"] != "driver":
        return {"error": "Drivers only"}
    return {"message": "Welcome driver"}