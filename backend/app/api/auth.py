from fastapi import APIRouter, HTTPException, Request, Header
from sqlalchemy.orm import Session
from fastapi import Depends
from app.schemas.user import UserLogin
from app.services.auth_service import authenticate_user
from app.core.jwt import create_access_token
from app.core.limiter import limiter
from app.services.redis_service import blacklist_token
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.db.session import get_db
from app.utils.response import success_response

router = APIRouter(prefix="/api/v1")

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": db_user.id, "role": db_user.role})

    return success_response(
        data={"access_token": token, "token_type": "bearer"},
        message="Login successful"
    )

@router.post("/logout")
async def logout(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = authorization.split(" ")[1]
    except:
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    await blacklist_token(token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return success_response(message="Logged out successfully")