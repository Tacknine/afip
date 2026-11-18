from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path("data/raw/nbs/nps2019/TZA_2019_NPD-SDD_v06_M_STATA12")

maize = pd.read_csv(
    "data/processed/maize_nps_candidates.csv",
    dtype={"household_id": str}
)

hh, meta = pyreadstat.read_dta(str(ROOT / "HH_SEC_A.dta"))

# T-0 location information
t0_file = pd.read_csv(
    "data/processed/maize_nps_location_audit.csv",
    dtype={"household_id": str}
)

current_columns = [
    "sdd_hhid", "loc_info",
    "hh_a01_1", "hh_a02_1",
    "hh_a03_1", "hh_a03_3a", "hh_a04_1"
]

current = hh[current_columns].copy()
current["sdd_hhid"] = current["sdd_hhid"].astype(str).str.strip()

# One row per household
data = maize[["household_id"]].drop_duplicates().merge(
    t0_file[
        ["household_id", "t0_region", "t0_district", "t0_ward_code"]
    ].drop_duplicates("household_id"),
    on="household_id",
    how="left",
    validate="one_to_one"
)

data = data.merge(
    current,
    left_on="household_id",
    right_on="sdd_hhid",
    how="left",
    validate="one_to_one"
)

print("=" * 65)
print("HOUSEHOLD LOCATION COMPARISON")
print("UNIQUE MAIZE HOUSEHOLDS:", len(data))

print("\nLOC_INFO COUNTS:")
print(data["loc_info"].value_counts(dropna=False).to_string())

print("\nCURRENT LOCATION COMPLETENESS:")
for col in [
    "hh_a01_1", "hh_a02_1", "hh_a03_1",
    "hh_a03_3a", "hh_a04_1"
]:
    print(f"{col}: {data[col].notna().sum()}/{len(data)}")

print("\nT-0 LOCATION COMPLETENESS:")
for col in ["t0_region", "t0_district", "t0_ward_code"]:
    print(f"{col}: {data[col].notna().sum()}/{len(data)}")

print("\nLOC_INFO VS CURRENT REGION:")
print(pd.crosstab(
    data["loc_info"],
    data["hh_a01_1"].notna(),
    margins=True
).to_string())

print("\nBOTH T-0 AND CURRENT REGION AVAILABLE:")
both_region = data[
    data["t0_region"].notna() &
    data["hh_a01_1"].notna()
]

print("RECORDS:", len(both_region))
print(
    "SAME REGION CODE:",
    (both_region["t0_region"] == both_region["hh_a01_1"]).sum()
)
print(
    "DIFFERENT REGION CODE:",
    (both_region["t0_region"] != both_region["hh_a01_1"]).sum()
)

print("\nBOTH T-0 AND CURRENT DISTRICT AVAILABLE:")
both_district = data[
    data["t0_district"].notna() &
    data["hh_a02_1"].notna()
]

print("RECORDS:", len(both_district))
print(
    "SAME DISTRICT CODE:",
    (both_district["t0_district"] == both_district["hh_a02_1"]).sum()
)
print(
    "DIFFERENT DISTRICT CODE:",
    (both_district["t0_district"] != both_district["hh_a02_1"]).sum()
)

print("\nAUDIT COMPLETE.")
