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

def upload_pdf(file_bytes: bytes, filename: str) -> dict:
    """
    Send a PDF to the backend /upload endpoint.
    Returns the JSON response dict.
    """
    response = requests.post(
        f"{BACKEND_URL}/api/v1/pdf_upload",
        files={"file": (filename, file_bytes, "application/pdf")},
    )
    response.raise_for_status()
    return response.json()

def stream_chat(question: str, history: list[dict]):
    """
    Send a question + history to /chat and yield tokens as they arrive.
    Uses requests streaming so the UI updates in real time.
    """
    with requests.post(
        f"{BACKEND_URL}/api/v1/rag_chat",
        json={"question": question, "history": history},
        stream=True,
    ) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                yield chunk.decode("utf-8")
