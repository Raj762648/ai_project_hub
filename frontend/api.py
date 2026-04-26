import os
import requests
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = "http://localhost:8000"
TIMEOUT = 180  # PDF fetching + LLM calls are slow on t2.micro


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


class APIError(Exception):
    pass


def run_research(query: str, session_id: str) -> dict:
    """POST /research → {session_id, query, response, steps}"""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/research",
            json={"query": query, "session_id": session_id},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        raise APIError("Request timed out — please retry.")
    except requests.exceptions.ConnectionError:
        raise APIError("Cannot connect to backend. Is it running on port 8000?")
    except requests.exceptions.HTTPError:
        raise APIError(f"Backend error {resp.status_code}: {resp.json().get('detail', 'unknown')}")


def get_history(session_id: str) -> list[dict]:
    try:
        return requests.get(f"{BACKEND_URL}/api/v1/get_history/{session_id}", timeout=10).json().get("history", [])
    except Exception:
        return []


def clear_history(session_id: str) -> bool:
    try:
        return requests.delete(f"{BACKEND_URL}/api/v1/del_history/{session_id}", timeout=10).ok
    except Exception:
        return False
    
def health_check() -> bool:
    try:
        return requests.get(f"{BACKEND_URL}/api/v1/agent_health", timeout=5).ok
    except Exception:
        return False

