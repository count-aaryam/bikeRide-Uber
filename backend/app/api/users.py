from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate
from app.services.user_service import create_user
from app.dependencies.auth import get_current_user
from app.core.limiter import limiter
from app.utils.response import success_response
from app.db.session import get_db

router = APIRouter(prefix="/api/v1")

@router.post("/users")
@limiter.limit("3/minute")
def signup(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    created_user = create_user(
        db=db,
        name=user.name,
        email=user.email,
        password=user.password,
        role=user.role,
        phone=user.phone
    )
    return success_response(
        data={"id": created_user.id},
        message="User created successfully"
    )

@router.get("/profile")
async def profile(current_user=Depends(get_current_user)):
    return success_response(data={"user": current_user})