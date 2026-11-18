from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path("data/raw/nbs/nps2019/TZA_2019_NPD-SDD_v06_M_STATA12")

CANDIDATES = Path("data/processed/maize_nps_candidates.csv")
HOUSEHOLD_FILE = ROOT / "HH_SEC_A.dta"

OUTPUT = Path("data/processed/maize_nps_location_audit.csv")

# 1. Read candidate maize records
maize = pd.read_csv(CANDIDATES, dtype={"household_id": str})

# 2. Read household location records
hh, meta = pyreadstat.read_dta(str(HOUSEHOLD_FILE))

location_columns = [
    "t0_region",
    "t0_district",
    "t0_ward_code"
]

required = ["sdd_hhid"] + location_columns

missing_columns = [c for c in required if c not in hh.columns]
if missing_columns:
    raise ValueError(f"Missing columns in HH_SEC_A: {missing_columns}")

hh = hh[required].copy()
hh["sdd_hhid"] = hh["sdd_hhid"].astype(str).str.strip()

# 3. Inspect duplicate household IDs
duplicates = hh[hh.duplicated("sdd_hhid", keep=False)]

print("=" * 60)
print("HOUSEHOLD LOCATION AUDIT")
print("HH RECORDS:", len(hh))
print("UNIQUE HOUSEHOLD IDs:", hh["sdd_hhid"].nunique())
print("ROWS WITH DUPLICATE IDs:", len(duplicates))
print("DUPLICATE HOUSEHOLD IDs:", duplicates["sdd_hhid"].nunique())

# 4. Build one location record per household.
# If an ID has conflicting non-missing location codes,
# exclude it from automatic matching.
conflicting_ids = []

for household_id, group in hh.groupby("sdd_hhid"):
    for column in location_columns:
        if group[column].dropna().nunique() > 1:
            conflicting_ids.append(household_id)
            break

conflicting_ids = set(conflicting_ids)

print("HOUSEHOLDS WITH CONFLICTING LOCATIONS:", len(conflicting_ids))

safe_hh = hh[~hh["sdd_hhid"].isin(conflicting_ids)].copy()

# Combine repeated rows where available location values do not conflict.
location_map = (
    safe_hh.groupby("sdd_hhid", as_index=False)[location_columns]
    .first()
)

print("SAFE UNIQUE LOCATION RECORDS:", len(location_map))

# 5. Match maize records to household locations
result = maize.merge(
    location_map,
    left_on="household_id",
    right_on="sdd_hhid",
    how="left",
    validate="many_to_one",
    indicator=True
)

matched = result["_merge"] == "both"

print("\n" + "=" * 60)
print("MAIZE LOCATION MATCHING")
print("MAIZE RECORDS:", len(maize))
print("MATCHED RECORDS:", int(matched.sum()))
print("UNMATCHED RECORDS:", int((~matched).sum()))
print("MATCH RATE: {:.2f}%".format(matched.mean() * 100))

print("\nLOCATION COMPLETENESS AMONG MATCHED RECORDS:")
for column in location_columns:
    available = result.loc[matched, column].notna().sum()
    total = matched.sum()
    print(f"{column}: {available}/{total}")

print("\nUNMATCHED HOUSEHOLD SAMPLE:")
print(
    result.loc[~matched, "household_id"]
    .drop_duplicates()
    .head(15)
    .to_string(index=False)
)

print("\nCONFLICTING HOUSEHOLD SAMPLE:")
print(list(conflicting_ids)[:15])

# 6. Save audit output; original files remain unchanged.
result.drop(columns=["sdd_hhid", "_merge"]).to_csv(OUTPUT, index=False)

print("\nOUTPUT:", OUTPUT)
print("AUDIT COMPLETED.")
