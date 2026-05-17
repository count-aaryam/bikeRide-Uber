from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api import users, auth, rides, driver, admin
from app.websocket import router as ws_router
from app.core.limiter import limiter
from app.core.redis import connect_redis, disconnect_redis

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await connect_redis()

@app.on_event("shutdown")
async def shutdown():
    await disconnect_redis()

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(rides.router)
app.include_router(driver.router)
app.include_router(admin.router)
app.include_router(ws_router.router)

@app.get("/")
def home():
    return {"status": "running"}