import os
import uuid
import io
import json
import logging
import uvicorn
from PIL import Image
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from schema import (ChurnPredictionRequest, ChurnPredictionResponse, 
                    XRayOutput,HealthResponse, ChatRequest, ResearchRequest, 
                    ResearchResponse, HistoryResponse, HistoryEntry)
from model  import predict_churn, load_churn_model, get_xray_model, xray_predict
from agents import run_research_agent, get_raw_history, clear_session
from rag import store_pdf_in_pinecone, stream_answer


load_dotenv(override=True)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)

# ── Lifespan: warm up model on startup ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Warming up model…")
    load_churn_model()
    logger.info("Model ready.")
    yield

app = FastAPI(
    title="Churn Prediction API",
    version="1.0.0",
    description="ML-powered churn prediction",
    lifespan=lifespan,
)

# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/api/v1/health", response_model=HealthResponse)
def health():
    try:
        load_churn_model()
        ready = True
    except Exception:
        ready = False
    return HealthResponse(status="ok", model_ready=ready)


@app.post(
    "/api/v1/churn_predict",
    response_model=ChurnPredictionResponse)
def churn_predict(req: ChurnPredictionRequest):
    try:
        result = predict_churn(req.model_dump())
        return ChurnPredictionResponse(**result)
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/api/v1/xray_predict", response_model=XRayOutput)
async def xray_predict_api(file: UploadFile = File(...)):

    try:
        image_bytes = await file.read()

        interp = get_xray_model()
        result = xray_predict(interp, image_bytes)

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.post("/api/v1/pdf_upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Accept a PDF file, embed its contents, and store in Pinecone.
    Returns the number of chunks stored.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    doc_id     = file.filename.replace(" ", "_").replace(".pdf", "")

    num_chunks = store_pdf_in_pinecone(file_bytes, doc_id)

    return {
        "message":    f"'{file.filename}' processed successfully.",
        "chunks_stored": num_chunks,
    }


@app.post("/api/v1/rag_chat")
def chat(request: ChatRequest):
    """
    Accept a question + conversation history.
    Stream back the answer token-by-token using Server-Sent Events.
    """
    def event_stream():
        for token in stream_answer(request.question, request.history):
            # Send each token as plain text so Streamlit can read it
            yield token

    return StreamingResponse(event_stream(), media_type="text/plain")


@app.post("/api/v1/research", response_model=ResearchResponse)
def run_agent(req: ResearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    session_id = req.session_id or str(uuid.uuid4())
    try:
        answer, steps = run_research_agent(req.query, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ResearchResponse(session_id=session_id, query=req.query, response=answer, steps=steps)


@app.get("/api/v1/get_history/{session_id}", response_model=HistoryResponse)
def get_history(session_id: str):
    history = get_raw_history(session_id)
    return HistoryResponse(session_id=session_id, history=[HistoryEntry(**h) for h in history])


@app.delete("/api/v1/del_history/{session_id}")
def delete_history(session_id: str):
    clear_session(session_id)
    return {"message": f"Session '{session_id}' cleared."}

@app.get("/api/v1/agent_health")
def health():
    return {"status": "ok"}
















     

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=False,
    )




