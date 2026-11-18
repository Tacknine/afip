from pathlib import Path
import pandas as pd
import pyreadstat

BASE = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

MODULES = {
    "AG_SEC_4A.dta": {
        "quantity": "ag4a_10_1",
        "unit": "ag4a_10_2",
    },
    "AG_SEC_4B.dta": {
        "quantity": "ag4b_10_1",
        "unit": "ag4b_10_2",
    },
}

for filename, columns in MODULES.items():
    print("\n" + "=" * 100)
    print(filename)
    print("=" * 100)

    df, meta = pyreadstat.read_dta(str(BASE / filename))
    maize = df[df["cropid"] == 11].copy()

    quantity = columns["quantity"]
    unit = columns["unit"]

    label_set = meta.variable_to_label.get(unit)
    labels = meta.value_labels.get(label_set, {}) if label_set else {}

    maize["unit_description"] = maize[unit].map(labels)
    maize["unit_description"] = maize["unit_description"].fillna(
        "UNKNOWN_OR_MISSING"
    )

    print("\nUNIT DISTRIBUTION:")
    print(
        maize["unit_description"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\nQUANTITY SUMMARY BY UNIT:")
    print(
        maize.groupby("unit_description")[quantity]
        .agg(["count", "min", "median", "mean", "max"])
        .to_string()
    )

    print("\nNON-KG RECORDS:")
    non_kg = maize[maize[unit] != 1]

    columns_to_show = [
        c for c in [
            "hhid", "plotnum", "cropid",
            quantity, unit, "unit_description"
        ]
        if c in maize.columns
    ]

    if len(non_kg):
        print(non_kg[columns_to_show].to_string(index=False))
    else:
        print("NONE")

    print("\nQUANTITY ABOVE 100:")
    large = maize[maize[quantity] > 100]

    if len(large):
        print(large[columns_to_show].to_string(index=False))
    else:
        print("NONE")

print("\nSEED UNIT AUDIT COMPLETED.")
print("RAW DATA WAS NOT MODIFIED.")
print("NO UNIT CONVERSION WAS ASSUMED.")
print("MODEL TRAINING WAS NOT STARTED.")
