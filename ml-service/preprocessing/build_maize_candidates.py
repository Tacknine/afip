from pathlib import Path
import pandas as pd
import pyreadstat

# ============================================================
# AFIP - MAIZE NPS DATASET BUILDER
# Source: Tanzania NPS 2019
# Crop code: 11 = MAIZE
# ============================================================

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

OUTPUT = Path(
    "data/processed/maize_nps_candidates.csv"
)

FILES = [
    {
        "filename": "AG_SEC_4A.dta",
        "module": "AG_SEC_4A",
        "harvested_var": "ag4a_19",
        "area_var": "ag4a_21",
        "quantity_var": "ag4a_27",
        "season": "LONG_RAINY_SEASON_2018",
    },
    {
        "filename": "AG_SEC_4B.dta",
        "module": "AG_SEC_4B",
        "harvested_var": "ag4b_19",
        "area_var": "ag4b_21",
        "quantity_var": "ag4b_28",
        "season": "LAST_COMPLETED_SHORT_RAINY_SEASON",
    },
]

frames = []


def classify_record(row):

    if row["harvested"] == 2:
        return "NOT_HARVESTED"

    if pd.isna(row["area_harvested_acres"]):
        return "MISSING_AREA"

    if pd.isna(row["quantity_reported"]):
        return "MISSING_QUANTITY"

    if row["area_harvested_acres"] < 0:
        return "NEGATIVE_AREA_REVIEW"

    if row["quantity_reported"] < 0:
        return "NEGATIVE_QUANTITY_REVIEW"

    if row["area_harvested_acres"] == 0:
        return "ZERO_AREA_REVIEW"

    if row["quantity_reported"] == 0:
        return "ZERO_QUANTITY_REVIEW"

    return "POSITIVE_VALUES_CANDIDATE"


for config in FILES:

    filename = config["filename"]

    module = config["module"]

    harvested_var = config["harvested_var"]

    area_var = config["area_var"]

    quantity_var = config["quantity_var"]

    season = config["season"]

    print("\nProcessing:", module)

    file_path = ROOT / filename

    df, meta = pyreadstat.read_dta(str(file_path))

    # Keep all maize observations.
    # Do not filter by harvest status, area or quantity.
    maize = df[df["cropid"] == 11].copy()

    result = pd.DataFrame({

        "source_file": filename,

        "source_module": module,

        "household_id": maize["sdd_hhid"],

        "plot_number": maize["plotnum"],

        "crop_code": maize["cropid"],

        "crop_name": "MAIZE",

        "season": season,

        "harvested": maize[harvested_var],

        "area_harvested_acres": maize[area_var],

        "area_unit": "ACRES",

        "quantity_reported": maize[quantity_var],

        "quantity_unit": "KG",

        "quantity_unit_evidence": (
            "QUESTIONNAIRE_SPECIFIES_KG_CONVERSION;"
            "INDIVIDUAL_CONVERSION_NOT_INDEPENDENTLY_VERIFIED"
        ),

        "harvested_variable": harvested_var,

        "area_variable": area_var,

        "quantity_variable": quantity_var,
    })

    result["quality_status"] = result.apply(
        classify_record,
        axis=1
    )

    frames.append(result)

    print("Records:", len(result))

    print("\nQuality status:")
    print(result["quality_status"].value_counts(dropna=False))


# Combine both agricultural modules.
output = pd.concat(
    frames,
    ignore_index=True
)

# Create output directory if necessary.
OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

# Save processed dataset.
output.to_csv(
    OUTPUT,
    index=False
)

# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 70)
print("AFIP MAIZE DATASET BUILD COMPLETE")
print("=" * 70)

print("Output:", OUTPUT)

print("Total maize records:", len(output))

print("\nRecords by season:")
print(output["season"].value_counts())

print("\nQuality status:")
print(
    output["quality_status"]
    .value_counts(dropna=False)
)

print("\nMissing values:")
print(output.isna().sum())

print("\nSample records:")
print(output.head(10).to_string(index=False))

print("\nRAW NPS FILES WERE NOT MODIFIED.")
print("MODEL TRAINING WAS NOT PERFORMED.")
