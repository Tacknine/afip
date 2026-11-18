from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path("data/raw/nbs/nps2019/TZA_2019_NPD-SDD_v06_M_STATA12")

hh, meta = pyreadstat.read_dta(str(ROOT / "HH_SEC_A.dta"))
maize = pd.read_csv(
    "data/processed/maize_nps_candidates.csv",
    dtype={"household_id": str}
)

columns = [
    "sdd_hhid",
    "loc_info",
    "hh_a01_1",
    "hh_a02_1",
    "hh_a03_1",
    "hh_a03_2",
    "hh_a03_3a",
    "hh_a04_1",
]

print("=" * 65)
print("CURRENT HOUSEHOLD LOCATION METADATA")

for col in columns:
    if col in hh.columns:
        print(f"\n{col}")
        print("Question:", meta.column_names_to_labels.get(col))
        label_name = meta.variable_to_label.get(col)
        print("Value labels:", meta.value_labels.get(label_name, {}))

print("\n" + "=" * 65)
print("HOUSEHOLD LOCATION COMPLETENESS")

for col in columns[1:]:
    if col in hh.columns:
        print(
            f"{col}: "
            f"{hh[col].notna().sum()}/{len(hh)} "
            f"({hh[col].notna().mean() * 100:.2f}%)"
        )

print("\nLOCATION VERIFICATION COUNTS:")
if "loc_info" in hh.columns:
    print(hh["loc_info"].value_counts(dropna=False).to_string())

print("\n" + "=" * 65)
print("MATCHING MAIZE RECORDS TO CURRENT LOCATIONS")

location_cols = [
    "sdd_hhid",
    "loc_info",
    "hh_a01_1",
    "hh_a02_1",
    "hh_a03_1",
    "hh_a03_2",
    "hh_a03_3a",
    "hh_a04_1",
]

available = [c for c in location_cols if c in hh.columns]
location = hh[available].copy()

location["sdd_hhid"] = location["sdd_hhid"].astype(str).str.strip()

result = maize.merge(
    location,
    left_on="household_id",
    right_on="sdd_hhid",
    how="left",
    validate="many_to_one",
    indicator=True
)

print("MAIZE RECORDS:", len(result))
print("MATCHED:", (result["_merge"] == "both").sum())

for col in available:
    if col not in ["sdd_hhid"]:
        count = result[col].notna().sum()
        print(f"{col}: {count}/{len(result)}")

print("\nSAMPLE CURRENT LOCATIONS:")
sample_cols = [
    c for c in [
        "household_id",
        "loc_info",
        "hh_a01_1",
        "hh_a02_1",
        "hh_a03_1",
        "hh_a03_3a",
        "hh_a04_1"
    ] if c in result.columns
]

print(result[sample_cols].head(15).to_string(index=False))
