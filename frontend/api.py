import os
import requests
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = "http://localhost:8000"


def churn_predict(endpoint,features: dict) -> dict:
    r = requests.post(BACKEND_URL+endpoint, json=features, timeout=15)
    r.raise_for_status()
    return r.json()

def xray_health_predict(endpoint,file_obj) -> dict:
    url = BACKEND_URL+endpoint

    files = {"file": ("image.jpg", file_obj, "image/jpeg")}
    r = requests.post(url, files=files ) # timeout=15
    r.raise_for_status()
    return r.json()

def health_check() -> dict:
    r = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
    r.raise_for_status()
    return r.json()


