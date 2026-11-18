"""AFIP ML Service - utabiri wa mavuno ya mahindi (modeli iliyofunzwa kwa data halisi)."""
import os
from contextlib import asynccontextmanager
from typing import Optional
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "yield_model.pkl")
bundle = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bundle
    if os.path.exists(MODEL_PATH):
        bundle = joblib.load(MODEL_PATH)
        print(f"Model loaded: {bundle['meta']['model_version']}", flush=True)
    else:
        print(f"WARNING: {MODEL_PATH} haipo. Endesha pipeline ya data halisi kisha train_model.py.", flush=True)
    yield

app = FastAPI(title="AFIP ML Service", version="2.0.0", lifespan=lifespan)

class YieldRequest(BaseModel):
    ndvi: float = Field(..., ge=-1.0, le=1.0)
    ph: Optional[float] = Field(None, ge=0.0, le=14.0)
    nitrogen: Optional[float] = Field(None, ge=0.0, description="g/kg")
    carbon: Optional[float] = Field(None, ge=0.0, description="g/kg")
    rainfall: Optional[float] = Field(None, ge=0.0, description="mm ya msimu")
    temperature: Optional[float] = Field(None, description="wastani wa C")

class YieldResponse(BaseModel):
    yield_t_ha: float
    interval_low: float
    interval_high: float
    confidence: Optional[float] = None
    model_version: str
    imputed_features: list[str]
    features_used: dict
    test_rmse: float

@app.get("/health")
def health():
    return {"status": "UP", "model_loaded": bundle is not None,
            "model_version": bundle["meta"]["model_version"] if bundle else None}

@app.get("/model-info")
def info():
    if bundle is None:
        raise HTTPException(503, "Model not loaded")
    return bundle["meta"]

@app.post("/predict", response_model=YieldResponse)
def predict(req: YieldRequest):
    if bundle is None:
        raise HTTPException(503, "Model not loaded")
    meta = bundle["meta"]
    feats = meta["features"]
    row = {f: getattr(req, f) for f in feats}
    imputed = [f for f, v in row.items() if v is None]
    pred = float(bundle["pipeline"].predict(pd.DataFrame([row], columns=feats))[0])
    lo_r, hi_r = meta["interval_residual_q10_q90"]
    return YieldResponse(
        yield_t_ha=round(max(pred, 0.0), 2),
        interval_low=round(max(pred + lo_r, 0.0), 2),
        interval_high=round(max(pred + hi_r, 0.0), 2),
        confidence=None,
        model_version=meta["model_version"],
        imputed_features=imputed,
        features_used={k: v for k, v in row.items() if v is not None},
        test_rmse=round(meta["test_metrics"]["rmse"], 3),
    )