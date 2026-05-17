from fastapi import Header, HTTPException
from app.core.jwt import verify_access_token
from app.services.redis_service import is_token_blacklisted

async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = authorization.split(" ")[1]
    except:
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    # Check if token was blacklisted via logout
    if await is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked. Please login again")

    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload

async def get_current_admin(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = authorization.split(" ")[1]
    except:
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    if await is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked. Please login again")

    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return payload