# app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "FastAPI is running on EC2!"}

@app.get("/health")
def health():
    return {"status": "ok"}
    