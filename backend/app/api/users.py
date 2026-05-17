# FastAPI utilities
# APIRouter -> groups related endpoints together
# Depends -> dependency injection system
# Request -> gives access to incoming HTTP request object
from fastapi import APIRouter, Depends, Request

# SQLAlchemy database session.
# Used to communicate with the database.
from sqlalchemy.orm import Session


# Pydantic schema for user signup validation.
# Ensures incoming request data matches required structure.
from app.schemas.user import UserCreate

# Service layer function responsible for creating users.
# Keeps business logic separated from route logic.
from app.services.user_service import create_user

# Authentication dependency.
# Used to fetch authenticated user from JWT/token.
from app.dependencies.auth import get_current_user

# Rate limiter object.
# Protects endpoint from abuse/spam requests.
from app.core.limiter import limiter

# Standardized API response formatter.
from app.utils.response import success_response

# Dependency that creates and provides database session.
from app.db.session import get_db


# Create API router.
# Every endpoint inside this router starts with:
# /api/v1
router = APIRouter(prefix="/api/v1")



# -------------USER SIGNUP / REGISTRATION ENDPOINT-----------


# POST request because we are creating a new resource (user).
@router.post("/users")

# Rate limiting:
# Only 3 requests allowed per minute from same client/IP.
#
# Helps prevent:
# - spam registrations
# - brute force attacks
# - server abuse
@limiter.limit("3/minute")

def signup(

    # Raw HTTP request object.
    # Required by limiter to identify client/IP.
    request: Request,

    # Request body validation using Pydantic schema.
    #
    # Expected JSON:
    # {
    #   "name": "Yash",
    #   "email": "yash@gmail.com",
    #   "password": "secret123",
    #   "role": "driver",
    #   "phone": "9999999999"
    # }
    #
    # FastAPI automatically:
    # - parses JSON
    # - validates data types
    # - creates UserCreate object
    user: UserCreate,

    # Inject database session automatically.
    db: Session = Depends(get_db)
):

    # Call service layer function to create new user.
    #
    # Inside this function it may:
    # - hash password
    # - validate email uniqueness
    # - create database entry
    # - commit transaction
    created_user = create_user(
        db=db,

        # Extract fields from validated Pydantic object.
        name=user.name,
        email=user.email,
        password=user.password,
        role=user.role,
        phone=user.phone
    )

    # Return standardized success response.
    return success_response(

        # Return newly created user's ID.
        data={
            "id": created_user.id
        },

        message="User created successfully"
    )


# ============================================================
# GET CURRENT USER PROFILE
# ============================================================

@router.get("/profile")
async def profile(

    # Dependency injection:
    # Automatically authenticates user before route executes.
    #
    # Probably:
    # 1. Reads JWT token from Authorization header
    # 2. Verifies token
    # 3. Extracts user information
    # 4. Returns user payload
    #
    # Example returned object:
    # {
    #   "user_id": 1,
    #   "email": "yash@gmail.com",
    #   "role": "driver"
    # }
    current_user=Depends(get_current_user)
):

    # Return authenticated user's profile data.
    return success_response(
        data={
            "user": current_user
        }
    )
