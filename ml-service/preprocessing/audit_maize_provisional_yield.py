from pathlib import Path
import pandas as pd

INPUT = Path("data/processed/maize_nps_candidates.csv")

OUTPUT = Path("data/processed/maize_yield_audit.csv")

df = pd.read_csv(INPUT)

# Only records with positive area and quantity
valid = df[
    (df["quality_status"] == "POSITIVE_VALUES_CANDIDATE")
].copy()

# Calculate provisional yield
valid["yield_kg_per_acre"] = (
    valid["quantity_reported"] /
    valid["area_harvested_acres"]
)

valid["yield_kg_per_hectare"] = (
    valid["yield_kg_per_acre"] * 2.47105
)

# Flag unusual values for investigation.
# Do not automatically remove them.
valid["yield_review_status"] = "NORMAL_REVIEW"

valid.loc[
    valid["yield_kg_per_hectare"] > 20000,
    "yield_review_status"
] = "HIGH_YIELD_REVIEW"

valid.loc[
    valid["yield_kg_per_hectare"] < 100,
    "yield_review_status"
] = "LOW_YIELD_REVIEW"

# Save audit output
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

valid.to_csv(OUTPUT, index=False)

print("=" * 70)
print("AFIP MAIZE PROVISIONAL YIELD AUDIT")
print("=" * 70)

print("Candidate records:", len(valid))

print("\nYield statistics (KG/ACRE):")
print(valid["yield_kg_per_acre"].describe())

print("\nYield statistics (KG/HECTARE):")
print(valid["yield_kg_per_hectare"].describe())

print("\nYield statistics by season:")
print(
    valid.groupby("season")["yield_kg_per_hectare"]
    .describe()
    .to_string()
)

print("\nYield review status:")
print(valid["yield_review_status"].value_counts())

print("\nHighest 15 yields:")
print(
    valid.nlargest(15, "yield_kg_per_hectare")[
        [
            "household_id",
            "plot_number",
            "season",
            "area_harvested_acres",
            "quantity_reported",
            "yield_kg_per_hectare",
            "yield_review_status",
        ]
    ].to_string(index=False)
)

print("\nLowest 15 yields:")
print(
    valid.nsmallest(15, "yield_kg_per_hectare")[
        [
            "household_id",
            "plot_number",
            "season",
            "area_harvested_acres",
            "quantity_reported",
            "yield_kg_per_hectare",
            "yield_review_status",
        ]
    ].to_string(index=False)
)

print("\nOutput:", OUTPUT)
print("\nRAW DATA AND CANDIDATE DATASET WERE NOT MODIFIED.")
print("NO MODEL TRAINING WAS PERFORMED.")
