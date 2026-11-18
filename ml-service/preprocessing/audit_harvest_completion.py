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

for name, c in configs.items():

    df, meta = pyreadstat.read_dta(str(ROOT / c["file"]))
    maize = df[df["cropid"] == 11].copy()
    harvested = maize[maize[c["harvest"]] == 1].copy()

    print("\n" + "=" * 75)
    print(name)
    print("=" * 75)

    if name == "AG_SEC_4B":
        print("\nAG4B_25 - FINISHED HARVEST")
        print(harvested["ag4b_25"].value_counts(dropna=False))

        label_set = meta.variable_to_label.get("ag4b_25")
        if label_set:
            print("VALUE LABELS:")
            print(meta.value_labels.get(label_set, {}))

    begin = c["begin"]
    end = c["end"]

    print("\nMissing month values:")
    print("Begin:", harvested[begin].isna().sum())
    print("End:", harvested[end].isna().sum())

    print("\nRecords with END = 0:")
    print(
        harvested[harvested[end] == 0][
            ["sdd_hhid", "plotnum", "cropid", begin, end]
        ].to_string(index=False)
    )

    print("\nDecember-to-February records:")
    print(
        harvested[
            (harvested[begin] == 12) &
            (harvested[end].isin([1, 2, 3]))
        ][
            ["sdd_hhid", "plotnum", "cropid", begin, end]
        ].to_string(index=False)
    )

print("\nHARVEST COMPLETION AUDIT COMPLETE.")
