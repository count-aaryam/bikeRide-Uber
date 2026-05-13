from fastapi import FastAPI
from app.api import users
from app.api import users, auth


app = FastAPI()

app.include_router(users.router)
app.include_router(users.router)
app.include_router(auth.router)


@app.get("/")
def home():
    return {"status": "running"}