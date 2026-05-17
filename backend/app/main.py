from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api import users, auth, rides, driver, admin
from app.websocket import router as ws_router
from app.core.limiter import limiter
from app.core.redis import connect_redis, disconnect_redis
from app.core.logging import logger
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.error_handler import (
    validation_exception_handler,
    global_exception_handler,
    sqlalchemy_exception_handler
)
from app.utils.background import (
    cleanup_stale_drivers_task,
    cleanup_empty_rooms_task,
    driver_heartbeat_check_task
)
import asyncio

app = FastAPI(title="BikeRide API", version="1.0.0")

# Middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup():
    await connect_redis()
    asyncio.create_task(cleanup_stale_drivers_task())
    asyncio.create_task(cleanup_empty_rooms_task())
    asyncio.create_task(driver_heartbeat_check_task())
    logger.info("BikeRide API started successfully")

@app.on_event("shutdown")
async def shutdown():
    await disconnect_redis()
    logger.info("BikeRide API shutting down")

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(rides.router)
app.include_router(driver.router)
app.include_router(admin.router)
app.include_router(ws_router.router)

@app.get("/")
def home():
    return {"success": True, "message": "BikeRide API running", "data": None}