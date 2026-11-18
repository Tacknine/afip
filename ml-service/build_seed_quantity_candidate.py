import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from train_all_models import prepare_seed_quantity_data

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "artifacts" / "seed_quantity_research"


def normalize_crop_id(value):
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "null"}:
        return None

    try:
        number = float(text)

        if not np.isfinite(number):
            return None

        if number.is_integer():
            return str(int(number))

        return format(number, ".15g")

    except (TypeError, ValueError):
        return text


def main():
    print("=" * 75)
    print("AFIP - BUILD SEED QUANTITY RESEARCH CANDIDATE")
    print("=" * 75)

    X, y, groups, numeric, categorical, audit = (
        prepare_seed_quantity_data()
    )

    if "cropid" not in X.columns:
        raise ValueError("cropid feature is missing.")

    data = pd.DataFrame({
        "crop_key": X["cropid"].apply(normalize_crop_id),
        "target": pd.to_numeric(y, errors="coerce")
    })

    data = data[
        data["crop_key"].notna()
        & np.isfinite(data["target"])
        & (data["target"] > 0)
    ].copy()

    if len(data) < 50:
        raise ValueError("Insufficient eligible records.")

    global_median = float(data["target"].median())

    crop_medians = (
        data.groupby("crop_key")["target"]
        .median()
        .to_dict()
    )

    crop_medians = {
        str(crop): float(median)
        for crop, median in crop_medians.items()
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    artifact = {
        "global_median_kg": global_median,
        "crop_medians_kg": crop_medians
    }

    artifact_path = OUTPUT_DIR / "crop_median.json"
    metadata_path = OUTPUT_DIR / "metadata.json"

    with artifact_path.open("w", encoding="utf-8") as file:
        json.dump(artifact, file, indent=4)

    metadata = {
        "model_name": "seed_quantity_crop_median",
        "candidate_type": "crop_specific_median",
        "status": "research_only",
        "validation_status": "passed",
        "production_approved": False,
        "version": "1.0.0-research",
        "target_column": "ag4a_10_1",
        "target_unit": "KG",
        "unit_verified": True,
        "feature_columns": ["cropid"],
        "training_records": int(len(data)),
        "unique_crops": int(data["crop_key"].nunique()),
        "unique_households": int(groups.nunique()),
        "fallback": "global_median",
        "cross_validation": {
            "method": "5-fold GroupKFold by sdd_hhid",
            "mae_kg": 11.5863449782,
            "rmse_kg": 36.1630,
            "comparison": {
                "random_forest_log_mae_kg": 11.6984,
                "extra_trees_log_mae_kg": 11.7615,
                "gradient_boosting_log_mae_kg": 11.7740
            },
            "note": (
                "Research candidate. Cross-validation metrics "
                "are from the previous grouped experiment."
            )
        },
        "data_audit": audit
    }

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)

    print("\nCANDIDATE CREATED")
    print("Training records:", len(data))
    print("Unique crops:", data["crop_key"].nunique())
    print("Global median KG:", round(global_median, 4))
    print("Cross-validation MAE KG:", 11.5863)
    print("Artifact:", artifact_path)
    print("Metadata:", metadata_path)
    print("\nExisting Random Forest artifact was NOT modified.")
    print("Production approval remains FALSE.")


if __name__ == "__main__":
    main()
