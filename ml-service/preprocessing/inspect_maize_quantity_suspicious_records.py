from pathlib import Path
import pandas as pd
import pyreadstat

root = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

checks = [
    ("AG_SEC_4A.dta", "ag4a_27", "ag4a_28"),
    ("AG_SEC_4B.dta", "ag4b_28", "ag4b_29"),
]

for filename, quantity, value in checks:

    df, meta = pyreadstat.read_dta(str(root / filename))

    print("\n" + "=" * 80)
    print(filename)
    print("=" * 80)

    print("\nQUANTITY LABEL:")
    print(meta.column_names_to_labels.get(quantity))

    print("\nVALUE LABEL:")
    print(meta.column_names_to_labels.get(value))

    print("\nHOUSEHOLD 0405-001-001:")
    columns = [
        "sdd_hhid", "plotnum", "cropid",
        quantity, value
    ]

    print(
        df[
            (df["sdd_hhid"] == "0405-001-001")
            & (df["cropid"] == 11)
        ][columns].to_string(index=False)
    )

    print("\nVALUE VARIABLE METADATA:")
    print(meta.variable_value_labels.get(value, {}))

print("\nRECORD INVESTIGATION COMPLETE.")
