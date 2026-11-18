from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "nbs"
    / "nps2019"
)

FEATURES = [
    "cropid",
    "ag4a_01",
    "ag4a_02",
    "ag4a_04",
    "ag4a_06",
    "ag4a_08",
]

TARGET = "ag4a_10_1"
UNIT = "ag4a_10_2"

print("=" * 80)
print("AFIP - REAL SEED QUANTITY PREDICTION RECORD AUDIT")
print("READ ONLY - RAW DATA WILL NOT BE MODIFIED")
print("=" * 80)

files = list(DATA_DIR.rglob("AG_SEC_4A.dta"))

if len(files) != 1:
    raise RuntimeError(
        f"Expected exactly one AG_SEC_4A.dta, found {len(files)}"
    )

file_path = files[0]

print("\nDATA FILE:", file_path)

df = pd.read_stata(
    file_path,
    convert_categoricals=False
)

required = FEATURES + [TARGET, UNIT]

missing_columns = [
    col for col in required
    if col not in df.columns
]

if missing_columns:
    raise RuntimeError(
        f"Missing required columns: {missing_columns}"
    )

for col in [TARGET, UNIT, "cropid"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

eligible = df[
    (df["cropid"] == 11)
    & (df[UNIT] == 1)
    & (df[TARGET] > 0)
].copy()

print("\nTOTAL DATASET ROWS:", len(df))
print("ELIGIBLE MAIZE KG RECORDS:", len(eligible))

complete = eligible.dropna(subset=FEATURES).copy()

print("RECORDS WITH ALL SIX FEATURES:", len(complete))

if complete.empty:
    raise RuntimeError(
        "No eligible maize record has all six required features."
    )

row = complete.iloc[0]

features = {}

for col in FEATURES:
    value = row[col]

    if hasattr(value, "item"):
        value = value.item()

    features[col] = value

target_value = float(row[TARGET])

print("\nSELECTED MODEL INPUT FEATURES:")
print(json.dumps(features, indent=4, ensure_ascii=False))

print("\nACTUAL SEED QUANTITY (KG):", target_value)

print("\nIMPORTANT:")
print("- Target was not included in model input.")
print("- Household identifiers were not included.")
print("- No unit conversion was performed.")
print("- Raw NPS data was not modified.")
print("- No prediction was performed by this script.")

print("\nAUDIT COMPLETED.")
