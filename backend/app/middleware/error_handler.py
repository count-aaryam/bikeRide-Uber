from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Catches Pydantic validation errors and returns clean messages."""
    errors = []
    for error in exc.errors():
        field = " → ".join(str(e) for e in error["loc"] if e != "body")
        message = error["msg"].replace("Value error, ", "")
        errors.append(f"{field}: {message}" if field else message)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation failed",
            "data": {"errors": errors}
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    """Catches any unhandled exception — prevents stack traces leaking to client."""
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "data": None
        }
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Catches DB errors cleanly."""
    logger.error(f"Database error on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Database error occurred",
            "data": None
        }
    )