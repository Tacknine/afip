import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from train_all_models import prepare_seed_quantity_data

print("=" * 75)
print("AFIP SEED QUANTITY - DIAGNOSTIC AUDIT")
print("=" * 75)

X, y, groups, numeric, categorical, audit = prepare_seed_quantity_data()

df = X.copy()
df["target_kg"] = y
df["household_id"] = groups

print("\n1. TARGET DISTRIBUTION")
print(df["target_kg"].describe(
    percentiles=[0.50, 0.75, 0.90, 0.95, 0.99]
).to_string())

print("\n2. TARGET EXTREME VALUES")
for threshold in [10, 20, 50, 100, 200, 500]:
    count = int((df["target_kg"] > threshold).sum())
    print(f"Above {threshold:>3} KG: {count:>4} ({count/len(df)*100:.2f}%)")

print("\n3. CROP DISTRIBUTION")
print(
    df.groupby("cropid", dropna=False)["target_kg"]
      .agg(["count", "median", "mean", "std", "min", "max"])
      .sort_values("count", ascending=False)
      .to_string()
)

print("\n4. FEATURE MISSING VALUES")
print(df[X.columns].isna().sum().to_string())

print("\n5. TARGET QUANTILES")
print(
    df.groupby("cropid", dropna=False)["target_kg"]
      .quantile([0.25, 0.50, 0.75, 0.90])
      .unstack()
      .to_string()
)

print("\n6. SAVED EVALUATION REPORT")
report_path = (
    "audit_results/seed_quantity_production_evaluation.json"
)

with open(report_path, "r", encoding="utf-8") as f:
    report = json.load(f)

print(json.dumps({
    "selected_algorithm": report["selected_algorithm"],
    "cv_results": report["cross_validation"],
    "test_metrics": report["test_metrics"],
    "baseline_mae_kg": report["baseline_mae_kg"],
    "ten_kg_test_records": report["ten_kg_test_records"]
}, indent=2))

print("\nDIAGNOSTIC AUDIT COMPLETED.")
print("RAW DATA WAS NOT MODIFIED.")
print("MODEL ARTIFACTS WERE NOT MODIFIED.")

