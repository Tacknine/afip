from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

configs = {
    "AG_SEC_4A": {
        "file": "AG_SEC_4A.dta",
        "quantity": "ag4a_27",
        "harvest": "ag4a_19",
        "area": "ag4a_21"
    },
    "AG_SEC_4B": {
        "file": "AG_SEC_4B.dta",
        "quantity": "ag4b_28",
        "harvest": "ag4b_19",
        "area": "ag4b_21"
    }
}

for name, c in configs.items():

    df, meta = pyreadstat.read_dta(str(ROOT / c["file"]))

    maize = df[df["cropid"] == 11].copy()

    print("\n" + "=" * 75)
    print(name)
    print("=" * 75)

    print("Total maize:", len(maize))

    for variable in [c["harvest"], c["area"], c["quantity"]]:

        print("\nVARIABLE:", variable)

        print(
            "QUESTION:",
            meta.column_labels[meta.column_names.index(variable)]
        )

        print(
            maize[variable]
            .describe()
        )

        print("Missing:", maize[variable].isna().sum())
        print("Zero:", (maize[variable] == 0).sum())
        print("Negative:", (maize[variable] < 0).sum())

    harvested = maize[maize[c["harvest"]] == 1].copy()

    print("\nHARVESTED RECORDS:", len(harvested))

    print("\nHARVESTED WITH MISSING QUANTITY:")
    print(harvested[c["quantity"]].isna().sum())

    print("\nHARVESTED WITH ZERO QUANTITY:")
    print((harvested[c["quantity"]] == 0).sum())

    print("\nHARVESTED WITH MISSING AREA:")
    print(harvested[c["area"]].isna().sum())

    print("\nHARVESTED WITH ZERO AREA:")
    print((harvested[c["area"]] == 0).sum())

print("\nQUANTITY AND AREA AUDIT COMPLETE.")
