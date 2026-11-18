from pathlib import Path
import sys
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from train_all_models import prepare_seed_quantity_data

MODEL_PATH = ROOT / "artifacts" / "seed_quantity" / "model.joblib"
METADATA_PATH = ROOT / "artifacts" / "seed_quantity" / "metadata.json"
OUTPUT_DIR = ROOT / "audit_results"

OUTPUT_DIR.mkdir(exist_ok=True)

def section(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)

section("AFIP - INDEPENDENT ARTIFACT EVALUATION")

# 1. Load existing artifact and metadata
model = joblib.load(MODEL_PATH)

with open(METADATA_PATH, encoding="utf-8") as f:
    metadata = json.load(f)

# 2. Reproduce data preparation
X, y, groups, numeric_features, categorical_features, audit = (
    prepare_seed_quantity_data()
)

# 3. Reproduce original split
splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=42
)

train_idx, test_idx = next(
    splitter.split(X, y, groups)
)

X_train = X.iloc[train_idx]
X_test = X.iloc[test_idx]
y_train = y.iloc[train_idx]
y_test = y.iloc[test_idx]

train_groups = set(groups.iloc[train_idx])
test_groups = set(groups.iloc[test_idx])

# 4. Verify split
section("1. RECONSTRUCTED SPLIT")

print("Eligible records:", len(X))
print("Training records:", len(X_train))
print("Testing records:", len(X_test))
print("Training households:", len(train_groups))
print("Testing households:", len(test_groups))
print("Household overlap:", len(train_groups.intersection(test_groups)))

# 5. Verify artifact features
section("2. FEATURE VERIFICATION")

model_features = list(
    getattr(model, "feature_names_in_", [])
)

print("Dataset features:", list(X.columns))
print("Model features:", model_features)
print("Feature match:", model_features == list(X.columns))

if model_features and model_features != list(X.columns):
    raise ValueError("Model features do not match prepared dataset.")

if len(X_test) != metadata.get("testing_rows"):
    raise ValueError("Testing row count does not match saved metadata.")

if len(X_train) != metadata.get("training_rows"):
    raise ValueError("Training row count does not match saved metadata.")

# 6. Predict held-out test records
section("3. HELD-OUT TEST PREDICTIONS")

predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
rmse = np.sqrt(mean_squared_error(y_test, predictions))
r2 = r2_score(y_test, predictions)

bias = float(np.mean(predictions - y_test.to_numpy()))

saved_metrics = metadata.get("metrics", {})

results = {
    "reconstructed_test_records": int(len(y_test)),
    "reconstructed_train_records": int(len(y_train)),
    "mae_kg": float(mae),
    "rmse_kg": float(rmse),
    "r2": float(r2),
    "prediction_bias_kg": bias,
    "saved_mae_kg": saved_metrics.get("mae_kg"),
    "saved_rmse_kg": saved_metrics.get("rmse_kg"),
    "saved_r2": saved_metrics.get("r2"),
    "mae_matches_metadata": bool(
        np.isclose(mae, saved_metrics.get("mae_kg", np.nan), atol=1e-6)
    ),
    "rmse_matches_metadata": bool(
        np.isclose(rmse, saved_metrics.get("rmse_kg", np.nan), atol=1e-6)
    ),
    "r2_matches_metadata": bool(
        np.isclose(r2, saved_metrics.get("r2", np.nan), atol=1e-6)
    )
}

for key, value in results.items():
    print(f"{key}: {value}")

# 7. Save record-level test predictions
prediction_df = X_test.copy()
prediction_df["actual_quantity_kg"] = y_test.to_numpy()
prediction_df["predicted_quantity_kg"] = predictions
prediction_df["error_kg"] = (
    prediction_df["predicted_quantity_kg"]
    - prediction_df["actual_quantity_kg"]
)
prediction_df["absolute_error_kg"] = prediction_df["error_kg"].abs()

prediction_df.to_csv(
    OUTPUT_DIR / "seed_quantity_reconstructed_test_predictions.csv",
    index=False
)

# 8. Inspect actual 10 KG records in test set
section("4. ACTUAL 10 KG RECORDS IN TEST SET")

ten_kg = prediction_df[
    np.isclose(prediction_df["actual_quantity_kg"], 10.0)
].copy()

print("10 KG test records:", len(ten_kg))

if len(ten_kg):
    print(
        ten_kg[
            [
                "actual_quantity_kg",
                "predicted_quantity_kg",
                "error_kg",
                "absolute_error_kg"
            ]
        ].to_string(index=False)
    )

ten_kg.to_csv(
    OUTPUT_DIR / "seed_quantity_10kg_test_predictions.csv",
    index=False
)

# 9. Final comparison and report
section("5. FINAL VALIDATION")

all_match = all([
    results["mae_matches_metadata"],
    results["rmse_matches_metadata"],
    results["r2_matches_metadata"]
])

results["all_metrics_match_metadata"] = all_match
results["household_overlap"] = len(
    train_groups.intersection(test_groups)
)
results["split_method"] = "GroupShuffleSplit"
results["random_state"] = 42
results["test_size"] = 0.20
results["model_path"] = str(MODEL_PATH)
results["metadata_path"] = str(METADATA_PATH)

with open(
    OUTPUT_DIR / "seed_quantity_reconstructed_evaluation.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("\nMETRICS MATCH SAVED METADATA:", all_match)

if all_match:
    print("RESULT: Reconstructed test metrics match saved metadata.")
else:
    print("RESULT: Metrics differ from saved metadata.")
    print("Investigate training provenance before making conclusions.")

print("\nOUTPUT FILES:")
print(OUTPUT_DIR / "seed_quantity_reconstructed_test_predictions.csv")
print(OUTPUT_DIR / "seed_quantity_10kg_test_predictions.csv")
print(OUTPUT_DIR / "seed_quantity_reconstructed_evaluation.json")

print("\nRAW DATA MODIFIED: NO")
print("MODEL RETRAINED: NO")
print("MODEL FILE MODIFIED: NO")
print("EVALUATION COMPLETED: YES")

