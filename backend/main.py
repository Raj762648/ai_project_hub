import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from PIL import Image
import io
import json
from dotenv import load_dotenv
from rag import store_pdf_in_pinecone, stream_answer

from schema import ChurnPredictionRequest, ChurnPredictionResponse, XRayOutput,HealthResponse, ChatRequest
from model  import predict_churn, load_churn_model, get_xray_model, xray_predict

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
     

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=False,
    )

