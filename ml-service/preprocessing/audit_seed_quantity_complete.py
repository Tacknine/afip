from pathlib import Path
import sys
import json
import warnings
import hashlib

import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from train_all_models import prepare_seed_quantity_data


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "seed_quantity"
MODEL_DIR = ROOT / "models"
OUTPUT_DIR = ROOT / "audit_results"

TARGET_VALUE = 10.0
RANDOM_STATE = 42
TEST_SIZE = 0.20

OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 100)
print("AFIP SEED QUANTITY - COMPREHENSIVE MODEL AUDIT")
print("READ ONLY - NO TRAINING - NO MODEL MODIFICATION")
print("=" * 100)


def section(title):
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


def sha256(path):
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def find_model_files():
    extensions = {".pkl", ".joblib"}

    return [
        p for p in MODEL_DIR.rglob("*")
        if p.is_file()
        and p.suffix.lower() in extensions
        and MODEL_NAME in p.name.lower()
    ] if MODEL_DIR.exists() else []


def find_metadata():
    candidates = [
        p for p in ROOT.rglob("*.json")
        if MODEL_NAME in p.name.lower()
        and "audit_results" not in str(p)
        and ".venv" not in str(p)
    ]

    return candidates


def main():

    # ========================================================
    # 1. DATA PREPARATION
    # ========================================================

    section("1. DATA PREPARATION")

    X, y, groups, numeric_features, categorical_features, audit = (
        prepare_seed_quantity_data()
    )

    print("Original rows:", audit["original_rows"])
    print("Eligible rows:", len(X))
    print("Unique households:", groups.nunique())
    print("Target:", audit["target"])
    print("Target unit:", audit["target_unit"])
    print("Features:", list(X.columns))

    # ========================================================
    # 2. REPRODUCE ORIGINAL SPLIT
    # ========================================================

    section("2. REPRODUCE ORIGINAL TRAINING/TESTING SPLIT")

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE
    )

    train_idx, test_idx = next(
        splitter.split(X, y, groups=groups)
    )

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    train_groups = set(groups.iloc[train_idx])
    test_groups = set(groups.iloc[test_idx])

    overlap = train_groups.intersection(test_groups)

    print("Training rows:", len(X_train))
    print("Testing rows:", len(X_test))
    print("Training households:", len(train_groups))
    print("Testing households:", len(test_groups))
    print("Household overlap:", len(overlap))

    if overlap:
        raise RuntimeError("Household leakage detected.")

    if len(X_test) < 20:
        raise RuntimeError("Testing set has fewer than 20 records.")

    # ========================================================
    # 3. ACTUAL 10 KG RECORDS
    # ========================================================

    section("3. ACTUAL 10 KG RECORD AUDIT")

    positions = np.flatnonzero(
        np.isclose(
            y.to_numpy(dtype=float),
            TARGET_VALUE,
            rtol=0,
            atol=1e-9
        )
    )

    records = []

    for pos in positions:

        records.append({
            "original_row_index": X.index[pos],
            "household_id": groups.iloc[pos],
            "actual_quantity_kg": y.iloc[pos],
            "split": (
                "TRAINING" if pos in set(train_idx)
                else "TESTING"
            ),
            **X.iloc[pos].to_dict()
        })

    records_df = pd.DataFrame(records)

    print("10 KG records:", len(records_df))

    if not records_df.empty:
        print(
            records_df["split"].value_counts().to_string()
        )

        records_df.to_csv(
            OUTPUT_DIR / "ten_kg_records.csv",
            index=False
        )

    # ========================================================
    # 4. MODEL FILE DISCOVERY
    # ========================================================

    section("4. SAVED MODEL DISCOVERY")

    model_files = find_model_files()

    if not model_files:
        print("No matching model file found.")
        print("Expected directory:", MODEL_DIR)
        print("Cannot continue model evaluation.")

        return

    for path in model_files:
        print("\nModel:", path)
        print("Size:", path.stat().st_size)
        print("SHA256:", sha256(path))
        print("Modified:", path.stat().st_mtime)

    # ========================================================
    # 5. METADATA DISCOVERY
    # ========================================================

    section("5. MODEL METADATA DISCOVERY")

    metadata_files = find_metadata()

    metadata_data = {}

    for path in metadata_files:

        try:
            with open(path, encoding="utf-8-sig") as file:
                data = json.load(file)

            print("\nMetadata file:", path)

            for key in [
                "model",
                "version",
                "model_version",
                "metrics",
                "training_rows",
                "testing_rows",
                "split_method",
                "data_audit",
                "feature_columns"
            ]:
                if key in data:
                    print(f"{key}: {data[key]}")

            if "seed_quantity" in path.name.lower():
                metadata_data = data

        except Exception as exc:
            print("Metadata read error:", path, exc)

    # ========================================================
    # 6. LOAD SAVED MODEL
    # ========================================================

    section("6. LOAD SAVED MODEL")

    selected_model = None

    for path in model_files:

        try:
            candidate = joblib.load(path)

            print("Loaded candidate:", path)
            print("Python type:", type(candidate).__name__)

            if hasattr(candidate, "predict"):
                selected_model = candidate
                print("Predict method: AVAILABLE")
                break

        except Exception as exc:
            print("Could not load:", path, exc)

    if selected_model is None:
        print("No compatible prediction model found.")
        return

    # ========================================================
    # 7. MODEL FEATURE VALIDATION
    # ========================================================

    section("7. FEATURE VALIDATION")

    if hasattr(selected_model, "feature_names_in_"):

        model_features = list(
            selected_model.feature_names_in_
        )

        print("Model features:", model_features)
        print("Audit features:", list(X_test.columns))

        if model_features != list(X_test.columns):
            raise RuntimeError(
                "Feature mismatch. Evaluation stopped."
            )

    else:
        print(
            "Model does not expose feature_names_in_. "
            "Checking prediction compatibility."
        )

    # ========================================================
    # 8. HELD-OUT TESTING PREDICTION
    # ========================================================

    section("8. HELD-OUT TESTING EVALUATION")

    predictions = np.asarray(
        selected_model.predict(X_test)
    ).reshape(-1)

    actual = y_test.to_numpy(dtype=float)

    if len(predictions) != len(actual):
        raise RuntimeError("Prediction count mismatch.")

    if not np.isfinite(predictions).all():
        raise RuntimeError("Non-finite model predictions.")

    mae = mean_absolute_error(actual, predictions)

    rmse = np.sqrt(
        mean_squared_error(actual, predictions)
    )

    r2 = r2_score(actual, predictions)

    bias = float(np.mean(predictions - actual))

    print("Testing records:", len(actual))
    print(f"MAE: {mae:.4f} KG")
    print(f"RMSE: {rmse:.4f} KG")
    print(f"R2: {r2:.4f}")
    print(f"Prediction bias: {bias:.4f} KG")

    # ========================================================
    # 9. ACTUAL VS PREDICTED
    # ========================================================

    section("9. ACTUAL VS PREDICTED ANALYSIS")

    evaluation = pd.DataFrame({
        "original_row_index": X_test.index,
        "household_id": groups.iloc[test_idx].to_numpy(),
        "actual_kg": actual,
        "predicted_kg": predictions
    })

    evaluation["absolute_error_kg"] = (
        evaluation["actual_kg"]
        - evaluation["predicted_kg"]
    ).abs()

    evaluation["signed_error_kg"] = (
        evaluation["predicted_kg"]
        - evaluation["actual_kg"]
    )

    evaluation["percentage_error"] = (
        evaluation["absolute_error_kg"]
        / evaluation["actual_kg"]
    ) * 100

    evaluation["residual"] = (
        evaluation["actual_kg"]
        - evaluation["predicted_kg"]
    )

    for column in X_test.columns:
        evaluation[column] = X_test[column].to_numpy()

    print(
        evaluation.sort_values(
            "absolute_error_kg",
            ascending=False
        ).head(20).to_string(index=False)
    )

    evaluation.to_csv(
        OUTPUT_DIR / "testing_predictions.csv",
        index=False
    )

    # ========================================================
    # 10. TESTING RECORDS WITH ACTUAL 10 KG
    # ========================================================

    section("10. HELD-OUT 10 KG RECORD PERFORMANCE")

    ten_kg_test = evaluation[
        np.isclose(
            evaluation["actual_kg"],
            TARGET_VALUE
        )
    ].copy()

    print("10 KG testing records:", len(ten_kg_test))

    if len(ten_kg_test):

        print(
            ten_kg_test[
                [
                    "original_row_index",
                    "household_id",
                    "actual_kg",
                    "predicted_kg",
                    "absolute_error_kg"
                ]
            ].to_string(index=False)
        )

    else:
        print("No 10 KG records in testing set.")

    # ========================================================
    # 11. ERROR DISTRIBUTION
    # ========================================================

    section("11. ERROR DISTRIBUTION")

    print(
        evaluation["absolute_error_kg"].describe().to_string()
    )

    print("\nMean prediction:", np.mean(predictions))
    print("Mean actual:", np.mean(actual))
    print("Maximum prediction:", np.max(predictions))
    print("Minimum prediction:", np.min(predictions))

    print("\nOverprediction records:",
          int((predictions > actual).sum()))

    print("Underprediction records:",
          int((predictions < actual).sum()))

    print("Exact predictions:",
          int(np.isclose(predictions, actual).sum()))

    # ========================================================
    # 12. TRAINING SET FIT - DIAGNOSTIC ONLY
    # ========================================================

    section("12. TRAINING SET DIAGNOSTIC")

    train_predictions = np.asarray(
        selected_model.predict(X_train)
    ).reshape(-1)

    train_mae = mean_absolute_error(
        y_train,
        train_predictions
    )

    train_rmse = np.sqrt(
        mean_squared_error(y_train, train_predictions)
    )

    train_r2 = r2_score(
        y_train,
        train_predictions
    )

    print(f"Training MAE: {train_mae:.4f} KG")
    print(f"Training RMSE: {train_rmse:.4f} KG")
    print(f"Training R2: {train_r2:.4f}")

    print("\nTraining vs Testing comparison:")
    print("Training MAE:", round(train_mae, 4))
    print("Testing MAE:", round(mae, 4))

    # ========================================================
    # 13. METADATA VS REPRODUCED SPLIT
    # ========================================================

    section("13. METADATA VS CURRENT SPLIT")

    print("Reproduced training rows:", len(X_train))
    print("Reproduced testing rows:", len(X_test))

    if metadata_data:

        print(
            "Metadata training rows:",
            metadata_data.get("training_rows")
        )

        print(
            "Metadata testing rows:",
            metadata_data.get("testing_rows")
        )

        print(
            "Metadata split method:",
            metadata_data.get("split_method")
        )

    else:
        print(
            "Specific seed_quantity metadata not identified. "
            "Review metadata files manually."
        )

    # ========================================================
    # 14. SAVE AUDIT REPORT
    # ========================================================

    section("14. SAVE AUDIT RESULTS")

    report = {
        "audit_type": "read_only",
        "model": MODEL_NAME,
        "dataset_rows": audit["original_rows"],
        "eligible_rows": len(X),
        "unique_households": groups.nunique(),
        "training_rows": len(X_train),
        "testing_rows": len(X_test),
        "household_overlap": len(overlap),
        "ten_kg_total": len(records_df),
        "ten_kg_training": int(
            (records_df["split"] == "TRAINING").sum()
        ) if len(records_df) else 0,
        "ten_kg_testing": int(
            (records_df["split"] == "TESTING").sum()
        ) if len(records_df) else 0,
        "testing_mae_kg": float(mae),
        "testing_rmse_kg": float(rmse),
        "testing_r2": float(r2),
        "testing_bias_kg": float(bias),
        "training_mae_kg": float(train_mae),
        "training_rmse_kg": float(train_rmse),
        "training_r2": float(train_r2),
        "model_file": str(model_files[0]),
        "model_sha256": sha256(model_files[0])
    }

    report_path = OUTPUT_DIR / "seed_quantity_audit.json"

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("Report:", report_path)
    print("Predictions:", OUTPUT_DIR / "testing_predictions.csv")
    print("10 KG records:", OUTPUT_DIR / "ten_kg_records.csv")

    section("FINAL STATUS")

    print("RAW DATA MODIFIED: NO")
    print("MODEL RETRAINED: NO")
    print("MODEL FILE MODIFIED: NO")
    print("HELD-OUT TESTING EVALUATED: YES")
    print("AUDIT COMPLETED: YES")

    print("=" * 100)


if __name__ == "__main__":
    main()

