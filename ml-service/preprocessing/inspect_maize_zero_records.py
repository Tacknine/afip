from pathlib import Path
import pyreadstat
import pandas as pd

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

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

for name, c in configs.items():

    df, meta = pyreadstat.read_dta(str(ROOT / c["file"]))

    maize = df[
        (df["cropid"] == 11) &
        (df[c["harvest"]] == 1)
    ].copy()

    zero_records = maize[
        (maize[c["area"]] == 0) |
        (maize[c["quantity"]] == 0)
    ]

    print("\n" + "=" * 70)
    print(name, "- ZERO VALUE RECORDS")
    print("=" * 70)

    if zero_records.empty:
        print("No zero-value records.")
    else:
        print(
            zero_records[
                [
                    "sdd_hhid",
                    "plotnum",
                    "cropid",
                    c["area"],
                    c["quantity"]
                ]
            ].to_string(index=False)
        )

print("\nZERO VALUE RECORD AUDIT COMPLETE.")
