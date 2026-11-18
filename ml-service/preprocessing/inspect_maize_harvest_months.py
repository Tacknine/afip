from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

files = {
    "AG_SEC_4A": {
        "file": "AG_SEC_4A.dta",
        "begin": "ag4a_24_1",
        "end": "ag4a_24_2",
        "harvest": "ag4a_19"
    },
    "AG_SEC_4B": {
        "file": "AG_SEC_4B.dta",
        "begin": "ag4b_24_1",
        "end": "ag4b_24_2",
        "harvest": "ag4b_19"
    }
}

for name, config in files.items():

    df, meta = pyreadstat.read_dta(
        str(ROOT / config["file"])
    )

    maize = df[df["cropid"] == 11].copy()

    print("\n" + "=" * 70)
    print(name, "- MAIZE HARVEST MONTH AUDIT")
    print("=" * 70)

    print("Total maize records:", len(maize))

    print("\nHARVEST STATUS:")
    print(maize[config["harvest"]].value_counts(dropna=False))

    harvested = maize[maize[config["harvest"]] == 1].copy()

    print("\nRecords with harvest status YES:", len(harvested))

    for variable in [config["begin"], config["end"]]:

        print("\nVARIABLE:", variable)

        print(
            harvested[variable]
            .value_counts(dropna=False)
            .sort_index()
        )

    print("\nHARVEST MONTH COMBINATIONS:")

    print(
        harvested.groupby(
            [config["begin"], config["end"]],
            dropna=False
        ).size().sort_values(ascending=False).head(20)
    )

print("\nMAIZE HARVEST MONTH AUDIT COMPLETE.")
