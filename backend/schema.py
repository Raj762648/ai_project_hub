from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

# ── Prediction Request ───────────────────────────────────────────────────────
class ChurnPredictionRequest(BaseModel):

    gender: str = Field(..., description="Gender of customer (Male/Female)")
    SeniorCitizen: str = Field(..., description="Is customer a senior citizen (Yes or No)")
    Partner: str = Field(..., description="Does customer have a partner (Yes/No)")
    Dependents: str = Field(..., description="Does customer have dependents (Yes/No)")
    tenure: int = Field(..., ge=0, le=100, description="Number of months customer has stayed")
    PhoneService: str = Field(..., description="Has phone service (Yes/No)")
    MultipleLines: str = Field(..., description="Multiple lines (Yes/No/No phone service)")
    InternetService: str = Field(..., description="Internet service type (DSL/Fiber optic/No)")
    OnlineSecurity: str = Field(..., description="Online security service (Yes/No/No internet service)")
    OnlineBackup: str = Field(..., description="Online backup (Yes/No/No internet service)")
    DeviceProtection: str = Field(..., description="Device protection (Yes/No/No internet service)")
    TechSupport: str = Field(..., description="Tech support (Yes/No/No internet service)")
    StreamingTV: str = Field(..., description="Streaming TV (Yes/No/No internet service)")
    StreamingMovies: str = Field(..., description="Streaming movies (Yes/No/No internet service)")
    Contract: str = Field(..., description="Contract type (Month-to-month/One year/Two year)")
    PaperlessBilling: str = Field(..., description="Paperless billing (Yes/No)")
    PaymentMethod: str = Field(..., description="Payment method type")
    MonthlyCharges: float = Field(..., ge=0, description="Monthly charges")
    TotalCharges: float = Field(..., ge=0, description="Total charges")


# ── Prediction Response ──────────────────────────────────────────────────────
class ChurnPredictionResponse(BaseModel):
    churn:       bool
    probability: float
    risk_level:  str     # "Low" | "Medium" | "High"

class XRayOutput(BaseModel):
    """Response from X-Ray classification endpoint."""
    label: str = Field(..., description="Predicted class label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for predicted class")
    probabilities: dict[str, float] = Field(..., description="Per-class probability scores")


# ── Health ───────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status:      str
    model_ready: bool
    version:     str = "1.0.0"

class ChatRequest(BaseModel):
    question: str
    history:  list[dict] = []   # list of {"role": ..., "content": ...} dicts


class ResearchRequest(BaseModel):
    query: str
    session_id: str | None = None


class ResearchResponse(BaseModel):
    session_id: str
    query: str
    response: str
    steps: list[str] = Field(default_factory=list)


class HistoryEntry(BaseModel):
    query: str
    response: str
    timestamp: str


class HistoryResponse(BaseModel):
    session_id: str
    history: list[HistoryEntry]
