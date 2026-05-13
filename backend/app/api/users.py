from fastapi import APIRouter
from app.schemas.user import UserCreate
from app.services.user_service import create_user
from fastapi import Depends
from app.dependencies.auth import get_current_user


router = APIRouter(prefix="/api/v1")

@router.post("/users")
def signup(user: UserCreate):
    created_user = create_user(
        name=user.name,
        email=user.email,
        password=user.password,
        role=user.role
    )

    return {
        "message": "User created",
        "id": created_user.id
    }
@router.get("/profile")
def profile(current_user = Depends(get_current_user)):
    return {
        "message": "Protected route accessed",
        "user": current_user
    }
@router.get("/driver-only")
def driver_route(current_user = Depends(get_current_user)):

    if current_user["role"] != "driver":
        return {"error": "Drivers only"}

    return {"message": "Welcome driver"}