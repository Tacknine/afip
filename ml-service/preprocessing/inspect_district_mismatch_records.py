from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

candidates = pd.read_csv(
    "data/processed/maize_nps_candidates.csv",
    dtype={"household_id": str}
)

hh, meta = pyreadstat.read_dta(
    str(ROOT / "HH_SEC_A.dta")
)

# Select location fields
location = hh[
    [
        "sdd_hhid",
        "t0_region",
        "t0_district",
        "hh_a01_1",
        "hh_a02_1",
        "loc_info"
    ]
].copy()

location = location.rename(
    columns={"sdd_hhid": "household_id"}
)

# Merge maize candidates with household locations
df = candidates.merge(
    location,
    on="household_id",
    how="left",
    validate="many_to_one"
)

# Keep records where both district codes exist but differ
mismatch = df[
    df["t0_district"].notna()
    & df["hh_a02_1"].notna()
    & (df["t0_district"] != df["hh_a02_1"])
].copy()

def get_label(variable, value):
    label_set = meta.variable_to_label.get(variable)

    if not label_set or pd.isna(value):
        return "MISSING"

    labels = meta.value_labels.get(label_set, {})
    return labels.get(value, labels.get(int(value), "UNKNOWN"))

print("\nDISTRICT MISMATCH RECORDS")
print("=" * 100)

for _, row in mismatch.iterrows():
    print("\nHousehold:", row["household_id"])
    print("Plot:", row["plot_number"])
    print("Season:", row["season"])

    print(
        "T0 region:",
        row["t0_region"],
        get_label("t0_region", row["t0_region"])
    )

    print(
        "Current region:",
        row["hh_a01_1"],
        get_label("hh_a01_1", row["hh_a01_1"])
    )

    print(
        "T0 district:",
        row["t0_district"],
        get_label("t0_district", row["t0_district"])
    )

    print(
        "Current district:",
        row["hh_a02_1"],
        get_label("hh_a02_1", row["hh_a02_1"])
    )

    print("Location verified flag:", row["loc_info"])

print("\nTOTAL MISMATCH RECORDS:", len(mismatch))
print("AUDIT COMPLETE.")
