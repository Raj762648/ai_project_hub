import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from PIL import Image
import io
from dotenv import load_dotenv

from schema import (
    ChurnPredictionRequest, ChurnPredictionResponse, XRayOutput,
    HealthResponse )
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=False,
    )

