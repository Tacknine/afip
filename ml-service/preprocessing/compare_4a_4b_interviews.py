from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

file_a = ROOT / "AG_SEC_4A.dta"
file_b = ROOT / "AG_SEC_4B.dta"

a, meta_a = pyreadstat.read_dta(str(file_a))
b, meta_b = pyreadstat.read_dta(str(file_b))

keys = ["sdd_hhid", "plotnum", "cropid"]

a = a.copy()
b = b.copy()

# Preserve interview identifiers
a["source_file"] = "AG_SEC_4A.dta"
b["source_file"] = "AG_SEC_4B.dta"

a = a[
    keys + [
        "interview__key",
        "ag4a_19",
        "ag4a_21",
        "ag4a_27"
    ]
].rename(columns={
    "ag4a_19": "harvest_flag",
    "ag4a_21": "area_acres",
    "ag4a_27": "quantity"
})

b = b[
    keys + [
        "interview__key",
        "ag4b_19",
        "ag4b_21",
        "ag4b_28"
    ]
].rename(columns={
    "ag4b_19": "harvest_flag",
    "ag4b_21": "area_acres",
    "ag4b_28": "quantity"
})

# Identify records whose household, plot and crop occur in both files
overlap = a.merge(
    b,
    on=keys,
    how="inner",
    suffixes=("_4A", "_4B")
)

print("\nOVERLAP SUMMARY")
print("=" * 90)
print("AG_SEC_4A rows:", len(a))
print("AG_SEC_4B rows:", len(b))
print("Matching household-plot-crop rows:", len(overlap))

print("\nINTERVIEW KEY COMPARISON")
print("=" * 90)

overlap["same_interview_key"] = (
    overlap["interview__key_4A"]
    == overlap["interview__key_4B"]
)

print(
    overlap["same_interview_key"]
    .value_counts(dropna=False)
)

print("\nOVERLAPPING RECORD DETAILS")
print("=" * 120)

columns = [
    "sdd_hhid",
    "plotnum",
    "cropid",
    "interview__key_4A",
    "interview__key_4B",
    "same_interview_key",
    "harvest_flag_4A",
    "harvest_flag_4B",
    "area_acres_4A",
    "area_acres_4B",
    "quantity_4A",
    "quantity_4B"
]

print(overlap[columns].to_string(index=False))

print("\nDUPLICATE KEYS WITHIN EACH FILE")
print("=" * 90)

print(
    "4A duplicate household-plot-crop rows:",
    a.duplicated(keys, keep=False).sum()
)

print(
    "4B duplicate household-plot-crop rows:",
    b.duplicated(keys, keep=False).sum()
)

print("\nAUDIT COMPLETE.")
