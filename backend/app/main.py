from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "running", "message": "Bike backend is live"}