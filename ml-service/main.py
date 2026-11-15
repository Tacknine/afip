"""
AFIP ML Service — serves the trained yield prediction model.
"""
import os
import joblib
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "yield_model.pkl")
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print(f"Model loaded from {MODEL_PATH}", flush=True)
    else:
        print(f"WARNING: Model not found at {MODEL_PATH}. Run train_model.py first.", flush=True)
    yield
    print("ML service shutting down", flush=True)

app = FastAPI(
    title="AFIP ML Service",
    description="Yield prediction API for Adaptive Farming Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

class YieldRequest(BaseModel):
    ndvi: float = Field(..., ge=0.0, le=1.0, description="Latest NDVI value")
    ph: Optional[float] = Field(None, ge=0.0, le=14.0, description="Soil pH")
    nitrogen: Optional[float] = Field(None, ge=0.0, description="Total nitrogen g/kg")
    carbon: Optional[float] = Field(None, ge=0.0, description="Organic carbon g/kg")
    rainfall: Optional[float] = Field(600.0, ge=0.0, description="Seasonal rainfall mm")
    temperature: Optional[float] = Field(25.0, description="Average temperature C")

class YieldResponse(BaseModel):
    yield_t_ha: float
    confidence: float
    model_version: str
    features_used: dict

@app.get("/health")
def health():
    return {
        "status": "UP",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
    }

@app.post("/predict", response_model=YieldResponse)
def predict(req: YieldRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    features = {
        'ndvi': req.ndvi,
        'ph': req.ph if req.ph is not None else 6.0,
        'nitrogen': req.nitrogen if req.nitrogen is not None else 1.5,
        'carbon': req.carbon if req.carbon is not None else 15.0,
        'rainfall': req.rainfall,
        'temperature': req.temperature,
    }

    X = np.array([[
        features['ndvi'],
        features['ph'],
        features['nitrogen'],
        features['carbon'],
        features['rainfall'],
        features['temperature'],
    ]])

    prediction = model.predict(X)[0]

    provided = sum(1 for v in [req.ndvi, req.ph, req.nitrogen, req.carbon] if v is not None)
    confidence = 0.5 + (provided / 4.0) * 0.4

    return YieldResponse(
        yield_t_ha=round(float(prediction), 2),
        confidence=round(float(confidence), 2),
        model_version="random-forest-v1.0.0",
        features_used=features,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)