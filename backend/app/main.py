from fastapi import FastAPI
from app.api import users
from app.api import users, auth
from app.api import rides

app = FastAPI()

app.include_router(users.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(rides.router)

@app.get("/")
def home():
    return {"status": "running"}