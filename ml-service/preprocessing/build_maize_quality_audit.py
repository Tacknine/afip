from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

OUTPUT = Path("data/processed")
OUTPUT.mkdir(parents=True, exist_ok=True)

configs = {
    "AG_SEC_4A": {
        "file": "AG_SEC_4A.dta",
        "area": "ag4a_21",
        "quantity": "ag4a_27",
        "harvest": "ag4a_19"
    },
    "AG_SEC_4B": {
        "file": "AG_SEC_4B.dta",
        "area": "ag4b_21",
        "quantity": "ag4b_28",
        "harvest": "ag4b_19"
    }
}

results = []

for module, config in configs.items():

    df, meta = pyreadstat.read_dta(
        str(ROOT / config["file"])
    )

    maize = df[df["cropid"] == 11].copy()

    for _, row in maize.iterrows():

        harvested = row[config["harvest"]] == 1
        area = row[config["area"]]
        quantity = row[config["quantity"]]

        if not harvested:
            status = "NOT_HARVESTED"

        elif pd.isna(area) or pd.isna(quantity):
            status = "MISSING_HARVEST_DATA"

        elif area < 0 or quantity < 0:
            status = "NEGATIVE_VALUE_REVIEW"

        elif area == 0 and quantity == 0:
            status = "BOTH_ZERO_REVIEW"

        elif area == 0:
            status = "ZERO_AREA_REVIEW"

        elif quantity == 0:
            status = "ZERO_QUANTITY_REVIEW"

        else:
            status = "POSITIVE_VALUES_CANDIDATE"

        results.append({
            "source_module": module,
            "household_id": row["sdd_hhid"],
            "plot_number": row["plotnum"],
            "crop_code": row["cropid"],
            "area_harvested_acres": area,
            "quantity_reported": quantity,
            "quantity_unit": "UNVERIFIED",
            "harvested": row[config["harvest"]],
            "quality_status": status
        })

audit = pd.DataFrame(results)

output_file = OUTPUT / "maize_data_quality_audit.csv"

audit.to_csv(output_file, index=False)

print("\nDATA QUALITY SUMMARY")
print("=" * 60)

print(
    audit.groupby(
        ["source_module", "quality_status"]
    ).size().to_string()
)

print("\nTOTAL RECORDS:", len(audit))
print("OUTPUT:", output_file)

print("\nDATA QUALITY AUDIT COMPLETE.")
