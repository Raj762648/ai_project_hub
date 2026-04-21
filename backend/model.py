import numpy as np
import pandas as pd
import logging
import os
import io
from PIL import Image
from functools import lru_cache
from dotenv import load_dotenv
load_dotenv(override=True)

from utils import download_model_from_s3
from utils import load_tflite_from_s3

logger = logging.getLogger(__name__)

# ── Singleton model loading ──────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_churn_model():
    """Loads model from S3 once and caches it in memory."""

    model = download_model_from_s3("churn_model.pkl")
    logger.info("Model loaded and ready.")
    return model


def predict_churn(features: dict) -> dict:
    """
    Takes a dict of feature values, returns churn label + probability.
    """
    import pandas as pd
    model = load_churn_model()
    feat = pd.DataFrame([features])
    prob      = model.predict_proba(feat)[:, 1]
    logger.info("Model prediction successfull.")
    label     = int(prob >= 0.5)
    risk      = "High" if prob >= 0.7 else ("Medium" if prob >= 0.4 else "Low")

    return {
        "churn":       bool(label),
        "probability": round(float(prob), 4),
        "risk_level":  risk,
    }

@lru_cache(maxsize=1)
def get_xray_model():
    return load_tflite_from_s3("xray_float32.tflite")


def preprocess_image(image_bytes):
    """Load and resize an X-ray image to match model input."""
    img = Image.open(io.BytesIO(image_bytes))\
              .convert("RGB")\
              .resize((224, 224))

    arr = np.array(img)
    return (arr / 255.0).astype(np.float32)[np.newaxis]


def xray_predict(interp,image):
    """Run inference and return class + confidence."""
    
    in_detail  = interp.get_input_details()[0]
    out_detail = interp.get_output_details()[0]

    # Preprocess
    input_data = preprocess_image(image)

    # Inference
    interp.set_tensor(in_detail["index"], input_data)
    interp.invoke()
    output = interp.get_tensor(out_detail["index"])

    # Parse probability (handle INT8 dequantization)
    prob = float(output[0][0])

    probabilities = {
        "PNEUMONIA": prob,
        "NORMAL": 1 - prob
        }

    label = max(probabilities, key=probabilities.get)
    confidence = probabilities[label]  # ✅ already 0–1

    return {
        "label": label,
        "confidence": confidence,
        "probabilities": probabilities
    }

