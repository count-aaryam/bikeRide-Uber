from fastapi import FastAPI
from app.api import users, auth, rides, driver
from app.websocket import router as ws_router

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(rides.router)
app.include_router(driver.router)
app.include_router(ws_router.router)

@app.get("/")
def home():
    return {"status": "running"}