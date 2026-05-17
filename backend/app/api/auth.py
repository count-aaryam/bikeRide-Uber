from fastapi import APIRouter, HTTPException, Request
from app.schemas.user import UserLogin
from app.services.auth_service import authenticate_user
from app.core.jwt import create_access_token
from app.core.limiter import limiter

router = APIRouter(prefix="/api/v1")

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, user: UserLogin):
    db_user = authenticate_user(user.email, user.password)

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": db_user.id, "role": db_user.role})

    return {
        "access_token": token,
        "token_type": "bearer"
    }