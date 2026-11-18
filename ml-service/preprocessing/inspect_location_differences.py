import pandas as pd
import pyreadstat

DATA_DIR = "data/processed"
RAW_DIR = "data/raw/nbs/nps2019/TZA_2019_NPD-SDD_v06_M_STATA12"

# Load maize location audit
maize = pd.read_csv(
    f"{DATA_DIR}/maize_nps_location_audit.csv"
)

# Load original household data
hh, meta = pyreadstat.read_dta(
    f"{RAW_DIR}/HH_SEC_A.dta"
)

# Rename household ID for consistent joining
hh = hh.rename(columns={"sdd_hhid": "household_id"})

# Select only required current-location fields
current_fields = [
    "household_id",
    "loc_info",
    "hh_a01_1",
    "hh_a02_1",
    "hh_a03_1",
    "hh_a03_3a",
    "hh_a04_1"
]

current = hh[current_fields].copy()

# Ensure one household has one location record
current = current.drop_duplicates("household_id")

# Merge T-0 and current location data
data = maize.merge(
    current,
    on="household_id",
    how="left",
    validate="many_to_one"
)

# Keep one record per household for comparison
data = data.drop_duplicates("household_id").copy()

print("=" * 60)
print("REGION CODE DIFFERENCES")
print("=" * 60)

both_region = data[
    data["t0_region"].notna() &
    data["hh_a01_1"].notna()
].copy()

region_diff = both_region[
    both_region["t0_region"] != both_region["hh_a01_1"]
]

print("Compared:", len(both_region))
print("Same:", len(both_region) - len(region_diff))
print("Different:", len(region_diff))

print("\nRegion difference combinations:")
print(
    region_diff[
        ["t0_region", "hh_a01_1"]
    ].value_counts(dropna=False)
)

print("\n" + "=" * 60)
print("DISTRICT CODE DIFFERENCES")
print("=" * 60)

both_district = data[
    data["t0_district"].notna() &
    data["hh_a02_1"].notna()
].copy()

district_diff = both_district[
    both_district["t0_district"] != both_district["hh_a02_1"]
]

print("Compared:", len(both_district))
print("Same:", len(both_district) - len(district_diff))
print("Different:", len(district_diff))

print("\nDistrict difference combinations:")
print(
    district_diff[
        ["t0_district", "hh_a02_1"]
    ].value_counts(dropna=False)
)

print("\nAUDIT COMPLETE.")
