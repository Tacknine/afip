"""AFIP ML Service - Seed Quantity prediction (production model)."""
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional
from pathlib import Path

# Hakikisha prediction.py inapatikana (iko kwenye ml-service root)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from prediction import (
    predict_seed_quantity,
    predict_maize_yield,
    recommend_crop,
    ModelUnavailableError,
    ModelValidationError,
    InvalidInputError,
    AFIPPredictionError,
)
from model_registry import list_models, get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Jaribu kupakia seed_quantity ili /health iwe fast
    try:
        predict_seed_quantity({
            "cropid": 11,
            "ag4a_01": 0.0, "ag4a_02": 0.0, "ag4a_04": 0.0,
            "ag4a_06": 0.0, "ag4a_08": 0.0,
        })
        print("seed_quantity model loaded", flush=True)
    except Exception as e:
        print(f"WARNING: seed_quantity not loadable: {e}", flush=True)
    yield


app = FastAPI(title="AFIP ML Service", version="3.0.0", lifespan=lifespan)


class SeedQuantityRequest(BaseModel):
    cropid: int = Field(..., description="NPS crop code (11=maize)")
    ag4a_01: Optional[float] = Field(None, description="Plot area / input 1")
    ag4a_02: Optional[float] = None
    ag4a_04: Optional[float] = None
    ag4a_06: Optional[float] = None
    ag4a_08: Optional[float] = None


class SeedQuantityResponse(BaseModel):
    seed_quantity_kg: float
    model: str
    model_version: str
    unit: str
    status: str


class YieldRequest(BaseModel):
    ndvi: float = Field(..., ge=-1.0, le=1.0)
    ph: Optional[float] = Field(None, ge=0.0, le=14.0)
    nitrogen: Optional[float] = Field(None, ge=0.0)
    carbon: Optional[float] = Field(None, ge=0.0)
    rainfall: Optional[float] = Field(None, ge=0.0)
    temperature: Optional[float] = None


@app.get("/health")
def health():
    try:
        r = predict_seed_quantity({
            "cropid": 11, "ag4a_01": 0.0, "ag4a_02": 0.0,
            "ag4a_04": 0.0, "ag4a_06": 0.0, "ag4a_08": 0.0,
        })
        return {"status": "UP", "model_loaded": True, "model": "seed_quantity",
                "model_version": r.get("model_version")}
    except Exception as e:
        return {"status": "DEGRADED", "model_loaded": False, "error": str(e)}


@app.get("/models")
def models():
    return list_models()


@app.get("/models/{name}")
def model_info(name: str):
    try:
        return get_model(name)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@app.post("/predict", response_model=SeedQuantityResponse)
def predict(req: SeedQuantityRequest):
    """Default prediction: seed quantity (production model)."""
    try:
        # Pydantic 2: model_dump; Pydantic 1: dict
        data = req.model_dump(exclude_none=True) if hasattr(req, "model_dump") else req.dict(exclude_none=True)
        # Jaza None kwa features zinazokosekana (model itatumia imputer)
        for f in ("ag4a_01", "ag4a_02", "ag4a_04", "ag4a_06", "ag4a_08"):
            data.setdefault(f, None)
        r = predict_seed_quantity(data)
        return SeedQuantityResponse(
            seed_quantity_kg=float(r["prediction"]),
            model=r["model"],
            model_version=r.get("model_version", "unknown"),
            unit=r.get("unit", "KG"),
            status=r["status"],
        )
    except ModelUnavailableError as e:
        raise HTTPException(503, f"Model unavailable: {e}")
    except ModelValidationError as e:
        raise HTTPException(503, f"Model invalid: {e}")
    except InvalidInputError as e:
        raise HTTPException(400, f"Invalid input: {e}")
    except AFIPPredictionError as e:
        raise HTTPException(500, f"Prediction failed: {e}")


@app.post("/predict/seed-quantity", response_model=SeedQuantityResponse)
def predict_sq(req: SeedQuantityRequest):
    return predict(req)


@app.post("/predict/yield")
def predict_yield(req: YieldRequest):
    """Yield prediction - NOT YET TRAINED. Returns 503."""
    try:
        data = req.model_dump(exclude_none=True) if hasattr(req, "model_dump") else req.dict(exclude_none=True)
        r = predict_maize_yield(data)
        return r
    except ModelUnavailableError:
        raise HTTPException(503, "maize_yield model not trained yet")
    except (ModelValidationError, InvalidInputError, AFIPPredictionError) as e:
        raise HTTPException(400, str(e))
