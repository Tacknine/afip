"""
AFIP - Agricultural Forecasting and Intelligence Platform
Prediction service for all four ML models.
"""

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"

LOGGER = logging.getLogger("AFIP.Prediction")

MODEL_CONFIG = {
    "seed_quantity": {
        "folder": "seed_quantity",
        "requires_verified_unit": True,
        "expected_unit": "KG",
    },
    "maize_yield": {
        "folder": "maize_yield",
        "requires_verified_unit": True,
        "expected_unit": None,
    },
    "crop_recommendation": {
        "folder": "crop_recommendation",
        "requires_verified_unit": False,
        "expected_unit": None,
    },
    "crop_production": {
        "folder": "crop_production",
        "requires_verified_unit": True,
        "expected_unit": None,
    },
}


class AFIPPredictionError(Exception):
    pass


class ModelUnavailableError(AFIPPredictionError):
    pass


class InvalidInputError(AFIPPredictionError):
    pass


class ModelValidationError(AFIPPredictionError):
    pass


_MODEL_CACHE = {}


def clear_model_cache():
    """Clear loaded models after replacing model artifacts."""
    _MODEL_CACHE.clear()


def _load_model(model_name):
    if model_name not in MODEL_CONFIG:
        raise ModelUnavailableError(
            f"Unknown model: {model_name}"
        )

    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    config = MODEL_CONFIG[model_name]

    model_dir = ARTIFACTS_DIR / config["folder"]
    model_path = model_dir / "model.joblib"
    metadata_path = model_dir / "metadata.json"

    if not model_path.is_file():
        raise ModelUnavailableError(
            f"Model file not found: {model_path}"
        )

    if not metadata_path.is_file():
        raise ModelUnavailableError(
            f"Metadata file not found: {metadata_path}"
        )

    try:
        with metadata_path.open(
            "r",
            encoding="utf-8"
        ) as file:
            metadata = json.load(file)

    except (OSError, json.JSONDecodeError) as exc:
        raise ModelValidationError(
            f"Cannot read metadata: {exc}"
        ) from exc

    if metadata.get("status") != "trained":
        raise ModelValidationError(
            f"{model_name} is not marked as trained."
        )

    if metadata.get("validation_status") != "passed":
        raise ModelValidationError(
            f"{model_name} has not passed validation."
        )

    features = metadata.get("feature_columns")

    if (
        not isinstance(features, list)
        or not features
        or not all(
            isinstance(x, str) and x.strip()
            for x in features
        )
    ):
        raise ModelValidationError(
            "Invalid feature_columns in metadata."
        )

    if config["requires_verified_unit"]:
        if metadata.get("unit_verified") is not True:
            raise ModelValidationError(
                f"{model_name}: target unit is not verified."
            )

        expected_unit = config["expected_unit"]
        actual_unit = metadata.get("target_unit")

        if expected_unit is not None:
            if actual_unit != expected_unit:
                raise ModelValidationError(
                    f"Expected unit {expected_unit}, "
                    f"received {actual_unit}."
                )
        elif not actual_unit:
            raise ModelValidationError(
                f"{model_name} has no verified target unit."
            )

    try:
        model = joblib.load(model_path)

    except Exception as exc:
        raise ModelUnavailableError(
            f"Could not load model: {exc}"
        ) from exc

    if not callable(getattr(model, "predict", None)):
        raise ModelValidationError(
            "Loaded artifact does not support predict()."
        )

    _MODEL_CACHE[model_name] = (model, metadata)

    LOGGER.info("Loaded model: %s", model_name)

    return model, metadata


def _prepare_input(input_data, feature_columns):
    if not isinstance(input_data, dict):
        raise InvalidInputError(
            "Input must be a dictionary."
        )

    missing = [
        column
        for column in feature_columns
        if column not in input_data
    ]

    if missing:
        raise InvalidInputError(
            "Missing features: " + ", ".join(missing)
        )

    selected = {}

    for column in feature_columns:
        value = input_data[column]

        if isinstance(value, (dict, list, tuple, set)):
            raise InvalidInputError(
                f"{column} must be a scalar."
            )

        if isinstance(value, (float, np.floating)):
            if not np.isfinite(value):
                raise InvalidInputError(
                    f"{column} must be finite."
                )

        selected[column] = value

    return pd.DataFrame(
        [selected],
        columns=feature_columns
    )


def _predict(model_name, input_data):
    model, metadata = _load_model(model_name)

    X = _prepare_input(
        input_data,
        metadata["feature_columns"]
    )

    try:
        prediction = model.predict(X)

    except Exception as exc:
        raise AFIPPredictionError(
            f"Prediction failed: {exc}"
        ) from exc

    if len(prediction) != 1:
        raise AFIPPredictionError(
            "Expected exactly one prediction."
        )

    value = prediction[0]

    if isinstance(value, np.generic):
        value = value.item()

    result = {
        "status": "success",
        "model": model_name,
        "prediction": value,
        "model_version": metadata.get("version", "unknown"),
    }

    if metadata.get("target_unit"):
        result["unit"] = metadata["target_unit"]

    return result


def predict_seed_quantity(input_data):
    """Predict seed quantity in verified KG."""
    result = _predict(
        "seed_quantity",
        input_data
    )

    result["description"] = "Predicted seed quantity"

    return result


def predict_maize_yield(input_data):
    """Predict maize yield using a verified target unit."""
    result = _predict(
        "maize_yield",
        input_data
    )

    result["description"] = "Predicted maize yield"

    return result


def recommend_crop(input_data, top_n=3):
    """Recommend crops using a validated classifier."""

    if not isinstance(top_n, int) or not 1 <= top_n <= 20:
        raise InvalidInputError(
            "top_n must be between 1 and 20."
        )

    model, metadata = _load_model(
        "crop_recommendation"
    )

    X = _prepare_input(
        input_data,
        metadata["feature_columns"]
    )

    try:
        prediction = model.predict(X)[0]

    except Exception as exc:
        raise AFIPPredictionError(
            f"Crop recommendation failed: {exc}"
        ) from exc

    if isinstance(prediction, np.generic):
        prediction = prediction.item()

    label_map = metadata.get("target_label_map", {})

    def display_name(code):
        return label_map.get(str(code), code)

    recommendations = []

    if callable(getattr(model, "predict_proba", None)):
        probabilities = model.predict_proba(X)[0]
        classes = model.classes_

        ranked = np.argsort(probabilities)[::-1][:top_n]

        for index in ranked:
            code = classes[index]

            if isinstance(code, np.generic):
                code = code.item()

            recommendations.append({
                "crop_code": code,
                "crop_name": display_name(code),
                "probability": round(
                    float(probabilities[index]), 6
                ),
            })

    else:
        recommendations.append({
            "crop_code": prediction,
            "crop_name": display_name(prediction),
            "probability": None,
        })

    return {
        "status": "success",
        "model": "crop_recommendation",
        "predicted_crop": display_name(prediction),
        "recommendations": recommendations,
        "model_version": metadata.get("version", "unknown"),
    }


def predict_crop_production(input_data):
    """Predict crop production in a verified unit."""

    result = _predict(
        "crop_production",
        input_data
    )

    result["description"] = "Predicted crop production"

    return result


def get_model_status():
    """Check availability and validation of all four models."""

    statuses = {}

    for model_name in MODEL_CONFIG:
        try:
            _, metadata = _load_model(model_name)

            statuses[model_name] = {
                "available": True,
                "status": "trained",
                "validation_status": "passed",
                "target_unit": metadata.get("target_unit"),
            }

        except AFIPPredictionError as exc:
            statuses[model_name] = {
                "available": False,
                "status": "unavailable",
                "reason": str(exc),
            }

    return statuses


def safe_prediction(function, input_data):
    """Return API-friendly error responses."""

    try:
        return function(input_data)

    except InvalidInputError as exc:
        return {
            "status": "invalid_input",
            "message": str(exc),
        }

    except ModelValidationError as exc:
        return {
            "status": "model_not_validated",
            "message": str(exc),
        }

    except ModelUnavailableError as exc:
        return {
            "status": "model_unavailable",
            "message": str(exc),
        }

    except AFIPPredictionError as exc:
        LOGGER.exception("Prediction error")

        return {
            "status": "prediction_error",
            "message": str(exc),
        }

    except Exception:
        LOGGER.exception("Unexpected prediction error")

        return {
            "status": "internal_error",
            "message": "Unexpected prediction error."
        }


if __name__ == "__main__":
    print("=" * 75)
    print("AFIP - PREDICTION SERVICE")
    print("=" * 75)

    print(
        json.dumps(
            get_model_status(),
            indent=4,
            default=str
        )
    )

    print("\nPREDICTION SERVICE CHECK COMPLETED.")



# ============================================================
# SEED QUANTITY - RESEARCH CANDIDATE
# Crop-specific median with global fallback.
# Does not replace the existing Random Forest model.
# ============================================================

def _normalize_candidate_crop_id(value):

    if value is None:
        raise InvalidInputError("cropid is required.")

    if isinstance(value, (dict, list, tuple, set)):
        raise InvalidInputError("cropid must be a scalar.")

    if isinstance(value, (float, np.floating)):
        if not np.isfinite(value):
            raise InvalidInputError("cropid must be finite.")

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "null"}:
        raise InvalidInputError("cropid must not be empty.")

    try:
        number = float(text)

        if not np.isfinite(number):
            raise InvalidInputError("cropid must be finite.")

        if number.is_integer():
            return str(int(number))

        return format(number, ".15g")

    except ValueError:
        return text


def predict_seed_quantity_candidate(input_data):
    """
    Research-only seed quantity prediction.

    Uses crop-specific training median.
    Uses global training median when cropid is unknown.
    """

    if not isinstance(input_data, dict):
        raise InvalidInputError("Input must be a dictionary.")

    if "cropid" not in input_data:
        raise InvalidInputError("Missing feature: cropid")

    crop_key = _normalize_candidate_crop_id(
        input_data["cropid"]
    )

    candidate_dir = (
        ARTIFACTS_DIR / "seed_quantity_research"
    )

    artifact_path = candidate_dir / "crop_median.json"
    metadata_path = candidate_dir / "metadata.json"

    if not artifact_path.is_file() or not metadata_path.is_file():
        raise ModelUnavailableError(
            "Seed quantity research candidate is unavailable."
        )

    try:
        with metadata_path.open("r", encoding="utf-8") as file:
            metadata = json.load(file)

        with artifact_path.open("r", encoding="utf-8") as file:
            artifact = json.load(file)

    except (OSError, json.JSONDecodeError) as exc:
        raise ModelValidationError(
            f"Cannot read research candidate artifacts: {exc}"
        ) from exc

    if metadata.get("model_name") != "seed_quantity_crop_median":
        raise ModelValidationError("Candidate metadata model name mismatch.")

    if metadata.get("status") != "research_only":
        raise ModelValidationError("Candidate is not marked research_only.")

    if metadata.get("production_approved") is not False:
        raise ModelValidationError(
            "Research candidate production approval flag is invalid."
        )

    crop_medians = artifact.get("crop_medians_kg")
    global_median = artifact.get("global_median_kg")

    if not isinstance(crop_medians, dict):
        raise ModelValidationError("Invalid crop median mapping.")

    try:
        global_median = float(global_median)

        if not np.isfinite(global_median) or global_median <= 0:
            raise ValueError("Invalid global median.")

    except (TypeError, ValueError) as exc:
        raise ModelValidationError(
            "Invalid global median in candidate artifact."
        ) from exc

    used_fallback = crop_key not in crop_medians

    prediction = (
        global_median
        if used_fallback
        else float(crop_medians[crop_key])
    )

    if not np.isfinite(prediction) or prediction <= 0:
        raise ModelValidationError(
            "Candidate produced an invalid prediction."
        )

    return {
        "status": "success",
        "model": "seed_quantity_crop_median",
        "model_version": metadata.get("version", "unknown"),
        "prediction": round(prediction, 4),
        "unit": "KG",
        "description": "Research estimate of seed quantity",
        "prediction_method": (
            "global_median_fallback"
            if used_fallback
            else "crop_specific_median"
        ),
        "cropid": crop_key,
        "production_approved": False,
        "research_only": True
    }
