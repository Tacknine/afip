from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/TZA_2019_NPD-SDD_v06_M_STATA12"
)

FILES = [
    {
        "file": "AG_SEC_4A.dta",
        "area": "ag4a_21",
        "quantity": "ag4a_27",
        "harvested": "ag4a_19",
    },
    {
        "file": "AG_SEC_4B.dta",
        "area": "ag4b_21",
        "quantity": "ag4b_28",
        "harvested": "ag4b_19",
    },
]

for item in FILES:
    df, meta = pyreadstat.read_dta(str(ROOT / item["file"]))

    maize = df[df["cropid"] == 11].copy()

    area = item["area"]
    quantity = item["quantity"]
    harvested = item["harvested"]

    print("\n" + "=" * 60)
    print("FILE:", item["file"])
    print("MAIZE RECORDS:", len(maize))

    print("\nHARVEST QUESTION:")
    print(meta.column_names_to_labels.get(harvested))

    print("HARVEST RESPONSE LABELS:")
    label_name = meta.variable_to_label.get(harvested)
    print(meta.value_labels.get(label_name, {}))

    print("\nHARVEST RESPONSE COUNTS:")
    print(maize[harvested].value_counts(dropna=False).to_string())

    print("\nAREA AND QUANTITY BY HARVEST RESPONSE:")
    print(
        maize.groupby(harvested, dropna=False)[[area, quantity]]
        .agg(["count", "mean", "min", "max"])
        .to_string()
    )

    print("\nQUANTITY VARIABLE LABEL:")
    print(meta.column_names_to_labels.get(quantity))

    print("\nSAMPLE RECORDS:")
    print(
        maize[
            ["sdd_hhid", "plotnum", harvested, area, quantity]
        ].head(20).to_string(index=False)
    )
