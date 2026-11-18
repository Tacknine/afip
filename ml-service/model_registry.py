import json
import logging
import math
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
REPORTS_DIR = BASE_DIR / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

REGISTRY_REPORT = REPORTS_DIR / "model_registry.json"
EVALUATION_REPORT = REPORTS_DIR / "evaluation_report.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("AFIP_MODEL_REGISTRY")

MODEL_NAMES = [
    "seed_quantity",
    "maize_yield",
    "crop_recommendation",
    "crop_production"
]

RESEARCH_MODEL_NAMES = [
    "seed_quantity_crop_median"
]


def read_json(path):
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        logger.error("Cannot read %s: %s", path, error)
        return None


def inspect_model(model_name, evaluations):

    model_dir = ARTIFACTS_DIR / model_name
    model_path = model_dir / "model.joblib"
    metadata_path = model_dir / "metadata.json"

    result = {
        "model_name": model_name,
        "available": False,
        "production_ready": False,
        "status": "unavailable",
        "version": None,
        "target_unit": None,
        "validation_status": None,
        "evaluation_recommendation": None,
        "reason": None
    }

    if not model_path.is_file():
        result["reason"] = "Model file does not exist."
        return result

    metadata = read_json(metadata_path)

    if metadata is None:
        result["reason"] = "Metadata missing or invalid."
        return result

    if metadata.get("model_name") != model_name:
        result["status"] = "invalid_metadata"
        result["reason"] = "Model name does not match metadata."
        return result

    result["version"] = metadata.get("version")
    result["target_unit"] = metadata.get("target_unit")
    result["validation_status"] = metadata.get(
        "validation_status"
    )

    if metadata.get("status") != "trained":
        result["status"] = "not_trained"
        result["reason"] = "Model is not marked as trained."
        return result

    if not metadata.get("feature_columns"):
        result["status"] = "invalid_metadata"
        result["reason"] = "Feature columns are missing."
        return result

    if model_name in [
        "seed_quantity",
        "maize_yield",
        "crop_production"
    ]:
        if metadata.get("unit_verified") is not True:
            result["status"] = "unit_not_verified"
            result["reason"] = "Target unit is not verified."
            return result

        if not metadata.get("target_unit"):
            result["status"] = "unit_missing"
            result["reason"] = "Target unit is missing."
            return result

    result["available"] = True

    evaluation = evaluations.get(model_name, {})
    evaluation_details = evaluation.get("evaluation", {})
    recommendation = evaluation_details.get("recommendation")

    result["evaluation_recommendation"] = recommendation

    if metadata.get("validation_status") != "passed":
        result["status"] = "trained_not_validated"
        result["reason"] = "Training validation did not pass."
        return result

    approved = (
        metadata.get("production_approved") is True
        and recommendation == "PRODUCTION_APPROVED"
    )

    if approved:
        result["production_ready"] = True
        result["status"] = "production_approved"
    else:
        result["status"] = "trained_requires_review"
        result["reason"] = (
            "Model requires stronger evaluation and explicit "
            "production approval."
        )

    return result


def inspect_research_model(model_name):

    candidate_dir = ARTIFACTS_DIR / "seed_quantity_research"

    artifact_path = candidate_dir / "crop_median.json"
    metadata_path = candidate_dir / "metadata.json"

    result = {
        "model_name": model_name,
        "available": False,
        "production_ready": False,
        "production_approved": False,
        "research_only": True,
        "candidate_type": None,
        "status": "unavailable",
        "version": None,
        "target_unit": None,
        "validation_status": None,
        "training_records": None,
        "unique_crops": None,
        "reason": None
    }

    if not artifact_path.is_file():
        result["reason"] = "Research artifact does not exist."
        return result

    if not metadata_path.is_file():
        result["reason"] = "Research metadata does not exist."
        return result

    metadata = read_json(metadata_path)
    artifact = read_json(artifact_path)

    if not isinstance(metadata, dict):
        result["reason"] = "Research metadata is invalid."
        return result

    if not isinstance(artifact, dict):
        result["reason"] = "Research artifact is invalid."
        return result

    if metadata.get("model_name") != model_name:
        result["status"] = "invalid_metadata"
        result["reason"] = "Research model name mismatch."
        return result

    if metadata.get("status") != "research_only":
        result["status"] = "invalid_metadata"
        result["reason"] = "Candidate is not marked research_only."
        return result

    if metadata.get("production_approved") is not False:
        result["status"] = "invalid_metadata"
        result["reason"] = (
            "Research candidate must not be production approved."
        )
        return result

    if metadata.get("candidate_type") != "crop_specific_median":
        result["status"] = "invalid_metadata"
        result["reason"] = "Unexpected candidate type."
        return result

    if metadata.get("target_unit") != "KG":
        result["status"] = "invalid_metadata"
        result["reason"] = "Expected target unit KG."
        return result

    if metadata.get("unit_verified") is not True:
        result["status"] = "unit_not_verified"
        result["reason"] = "Candidate target unit is not verified."
        return result

    if not metadata.get("feature_columns"):
        result["status"] = "invalid_metadata"
        result["reason"] = "Feature columns are missing."
        return result

    crop_medians = artifact.get("crop_medians_kg")
    global_median = artifact.get("global_median_kg")

    if not isinstance(crop_medians, dict) or not crop_medians:
        result["status"] = "invalid_artifact"
        result["reason"] = "Crop median mapping is invalid."
        return result

    try:
        global_median = float(global_median)

        if not math.isfinite(global_median) or global_median <= 0:
            raise ValueError("Invalid global median.")

        for value in crop_medians.values():
            number = float(value)

            if not math.isfinite(number) or number <= 0:
                raise ValueError("Invalid crop median.")

    except (TypeError, ValueError):
        result["status"] = "invalid_artifact"
        result["reason"] = "Median values must be finite and positive."
        return result

    result.update({
        "available": True,
        "status": "research_only",
        "version": metadata.get("version"),
        "candidate_type": metadata.get("candidate_type"),
        "target_unit": metadata.get("target_unit"),
        "validation_status": metadata.get("validation_status"),
        "training_records": metadata.get("training_records"),
        "unique_crops": metadata.get("unique_crops"),
        "reason": (
            "Experimental candidate. Requires further evaluation "
            "and explicit production approval."
        )
    })

    return result


def list_models():

    evaluation_data = read_json(EVALUATION_REPORT) or {}
    evaluations = evaluation_data.get("models", {})

    registry = {
        "platform": "AFIP",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "models": {},
        "research_models": {}
    }

    for model_name in MODEL_NAMES:
        registry["models"][model_name] = inspect_model(
            model_name,
            evaluations
        )

    for model_name in RESEARCH_MODEL_NAMES:
        registry["research_models"][model_name] = (
            inspect_research_model(model_name)
        )

    return registry


def get_model(model_name):

    if model_name in MODEL_NAMES:
        result = list_models()["models"][model_name]

    elif model_name in RESEARCH_MODEL_NAMES:
        result = list_models()["research_models"][model_name]

    else:
        raise ValueError(f"Unknown model: {model_name}")

    if not result["available"]:
        raise RuntimeError(result["reason"])

    return result


def get_research_models():

    registry = list_models()

    return {
        name: details
        for name, details in registry["research_models"].items()
        if details["available"]
    }


def get_production_models():

    registry = list_models()

    return {
        name: details
        for name, details in registry["models"].items()
        if details["production_ready"]
    }


def save_registry():

    registry = list_models()

    with open(
        REGISTRY_REPORT,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            registry,
            file,
            indent=4,
            ensure_ascii=False
        )

    return registry


def print_registry():

    registry = save_registry()

    print("=" * 75)
    print("AFIP MODEL REGISTRY")
    print("=" * 75)

    print("\nPRODUCTION MODELS")

    for name, details in registry["models"].items():

        print(f"\nMODEL: {name.upper()}")
        print("Available:", details["available"])
        print("Production ready:", details["production_ready"])
        print("Status:", details["status"])
        print("Version:", details["version"])
        print("Target unit:", details["target_unit"])
        print("Evaluation:", details["evaluation_recommendation"])

        if details["reason"]:
            print("Reason:", details["reason"])

    print("\nRESEARCH MODELS")

    for name, details in registry["research_models"].items():

        print(f"\nMODEL: {name.upper()}")
        print("Available:", details["available"])
        print("Research only:", details["research_only"])
        print("Production approved:", details["production_approved"])
        print("Status:", details["status"])
        print("Version:", details["version"])
        print("Target unit:", details["target_unit"])
        print("Training records:", details["training_records"])
        print("Unique crops:", details["unique_crops"])

        if details["reason"]:
            print("Reason:", details["reason"])

    production_models = get_production_models()
    research_models = get_research_models()

    print("\n" + "=" * 75)
    print("PRODUCTION-READY MODELS:", len(production_models))
    print("RESEARCH CANDIDATES:", len(research_models))
    print("Registry report:", REGISTRY_REPORT)
    print("REGISTRY CHECK COMPLETED.")


if __name__ == "__main__":
    print_registry()
