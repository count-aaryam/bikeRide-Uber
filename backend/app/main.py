from fastapi import FastAPI
from app.api import users, auth, rides
from app.api import driver

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(rides.router)
app.include_router(driver.router)

@app.get("/")
def home():
    return {"status": "running"}