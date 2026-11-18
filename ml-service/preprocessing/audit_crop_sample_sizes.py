import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from train_all_models import prepare_seed_quantity_data

X, y, groups, numeric, categorical, audit = prepare_seed_quantity_data()

df = X[["cropid"]].copy()
df["target_kg"] = y
df["household_id"] = groups

summary = df.groupby("cropid").agg(
    records=("target_kg", "size"),
    households=("household_id", "nunique"),
    median_kg=("target_kg", "median"),
    mean_kg=("target_kg", "mean"),
    std_kg=("target_kg", "std"),
    minimum_kg=("target_kg", "min"),
    maximum_kg=("target_kg", "max")
)

summary["records_percentage"] = (
    summary["records"] / len(df) * 100
)

summary["household_records_ratio"] = (
    summary["records"] / summary["households"]
)

summary = summary.sort_values(
    "records",
    ascending=False
)

print("\n" + "=" * 85)
print("AFIP CROP SAMPLE SIZE AND HOUSEHOLD AUDIT")
print("=" * 85)

print(summary.round(2).to_string())

print("\nCROP SAMPLE SIZE GROUPS")

print("At least 100 records:", (summary["records"] >= 100).sum())
print("50-99 records:", (
    (summary["records"] >= 50) &
    (summary["records"] < 100)
).sum())
print("20-49 records:", (
    (summary["records"] >= 20) &
    (summary["records"] < 50)
).sum())
print("Below 20 records:", (summary["records"] < 20).sum())

print("\nTOTAL CROPS:", len(summary))
print("TOTAL RECORDS:", len(df))
print("TOTAL HOUSEHOLDS:", df["household_id"].nunique())

output = Path("audit_results/crop_sample_size_audit.csv")
summary.to_csv(output)

print("\nSaved:", output)
print("RAW DATA WAS NOT MODIFIED.")
print("MODEL ARTIFACTS WERE NOT MODIFIED.")
