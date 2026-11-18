from pathlib import Path
import pandas as pd
import re

DATA_DIR = Path(
    "data/raw/nbs/nps2019/TZA_2019_NPD-SDD_v06_M_STATA12"
)
OUTPUT_DIR = Path("reports")
OUTPUT_DIR.mkdir(exist_ok=True)

KEYWORDS = [
    "crop", "harvest", "production", "yield", "quantity",
    "area", "plot", "seed", "fertil", "manure", "soil",
    "irrigat", "pestic", "herbicide", "insecticide",
    "rain", "water", "land", "plant", "cultivat",
    "livestock", "value", "unit", "maize"
]

all_rows = []

print("=" * 100)
print("NPS 2019 AGRICULTURE DATASET VARIABLE AUDIT")
print("RAW DATA WILL NOT BE MODIFIED")
print("=" * 100)

files = sorted(DATA_DIR.glob("AG_SEC_*.dta"))

for file in files:
    print("\n" + "=" * 100)
    print(f"FILE: {file.name}")

    try:
        reader = pd.read_stata(
            file,
            iterator=True,
            convert_categoricals=False
        )

        df = reader.read()
        labels = reader.variable_labels()

        print(f"ROWS: {len(df):,}")
        print(f"COLUMNS: {len(df.columns)}")

        id_columns = [
            col for col in df.columns
            if any(term in col.lower()
                   for term in ["hhid", "plot", "cropid", "cluster", "region"])
        ]

        print("\nPOSSIBLE IDENTIFIER COLUMNS:")
        print(id_columns if id_columns else "None detected by name")

        print("\nRELEVANT VARIABLES AND QUESTION LABELS:")

        for col in df.columns:
            label = str(labels.get(col, ""))
            searchable = f"{col} {label}".lower()

            if any(keyword in searchable for keyword in KEYWORDS):
                print(f"{col:25} | {label}")

                all_rows.append({
                    "file": file.name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "variable": col,
                    "label": label,
                    "dtype": str(df[col].dtype),
                    "missing": int(df[col].isna().sum()),
                    "unique_values": int(df[col].nunique(dropna=True))
                })

    except Exception as exc:
        print(f"ERROR READING FILE: {exc}")

output = OUTPUT_DIR / "agriculture_variable_inventory.csv"

inventory = pd.DataFrame(all_rows)
inventory.to_csv(output, index=False, encoding="utf-8-sig")

print("\n" + "=" * 100)
print("AGRICULTURE VARIABLE AUDIT COMPLETED")
print(f"VARIABLE INVENTORY: {output}")
print("RAW DATA WAS NOT MODIFIED")
print("NO UNIT CONVERSION WAS ASSUMED")
print("MODEL TRAINING WAS NOT STARTED")
print("=" * 100)
