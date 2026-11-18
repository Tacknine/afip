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

location = hh[
    [
        "sdd_hhid",
        "t0_region",
        "t0_district",
        "hh_a01_1",
        "hh_a02_1",
        "loc_info"
    ]
].rename(columns={"sdd_hhid": "household_id"})

df = candidates.merge(
    location,
    on="household_id",
    how="left",
    validate="many_to_one"
)

mismatch = df[
    df["t0_district"].notna()
    & df["hh_a02_1"].notna()
    & (df["t0_district"] != df["hh_a02_1"])
].copy()

print("\n1. RECORDS BY SOURCE FILE")
print(mismatch.groupby("source_file").size())

print("\n2. RECORDS BY DISTRICT PAIR")
pairs = mismatch.groupby(
    ["t0_district", "hh_a02_1"]
).size().reset_index(name="records")

print(pairs.to_string(index=False))

print("\n3. DUPLICATE HOUSEHOLD-PLOT COMBINATIONS")
duplicates = mismatch[
    mismatch.duplicated(
        subset=["household_id", "plot_number"],
        keep=False
    )
].sort_values(["household_id", "plot_number", "source_file"])

if duplicates.empty:
    print("No repeated household-plot combinations.")
else:
    print(
        duplicates[
            [
                "source_file",
                "household_id",
                "plot_number",
                "season",
                "t0_district",
                "hh_a02_1"
            ]
        ].to_string(index=False)
    )

print("\n4. LOCATION VERIFICATION STATUS")
print(mismatch["loc_info"].value_counts(dropna=False))

print("\nTOTAL MISMATCH ROWS:", len(mismatch))
print("UNIQUE HOUSEHOLDS:", mismatch["household_id"].nunique())
print("AUDIT COMPLETE.")
