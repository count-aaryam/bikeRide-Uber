from fastapi import FastAPI
from app.api import users

app = FastAPI()

app.include_router(users.router)

@app.get("/")
def home():
    return {"status": "running"}