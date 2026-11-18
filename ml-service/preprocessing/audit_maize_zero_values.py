from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path("data/raw/nbs/nps2019/TZA_2019_NPD-SDD_v06_M_STATA12")

FILES = [
    ("AG_SEC_4A.dta", "ag4a_19", "ag4a_21", "ag4a_27"),
    ("AG_SEC_4B.dta", "ag4b_19", "ag4b_21", "ag4b_28"),
]

for filename, harvested, area, quantity in FILES:
    df, meta = pyreadstat.read_dta(str(ROOT / filename))

    maize = df[
        (df["cropid"] == 11) &
        (df[harvested] == 1)
    ].copy()

    zero_records = maize[
        (maize[area] <= 0) |
        (maize[quantity] <= 0)
    ]

    print("\n" + "=" * 60)
    print("FILE:", filename)
    print("MAIZE HARVESTED:", len(maize))
    print("ZERO/INVALID RECORDS:", len(zero_records))

    if not zero_records.empty:
        print(
            zero_records[
                ["sdd_hhid", "plotnum", area, quantity]
            ].to_string(index=False)
        )

    print("\nPOSITIVE AREA AND QUANTITY:")
    valid = maize[
        (maize[area] > 0) &
        (maize[quantity] > 0)
    ]

    print("VALID RECORDS:", len(valid))
    print("EXCLUDED RECORDS:", len(maize) - len(valid))
