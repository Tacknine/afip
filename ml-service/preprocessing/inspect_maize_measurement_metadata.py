from pathlib import Path
import pyreadstat
import pandas as pd

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

modules = {
    "AG_SEC_4A": {
        "file": "AG_SEC_4A.dta",
        "variables": [
            "ag4a_10_1",
            "ag4a_10a_1",
            "ag4a_10c_1",
            "ag4a_17",
            "ag4a_19",
            "ag4a_21",
            "ag4a_22",
            "ag4a_26",
            "ag4a_27",
            "ag4a_28",
        ],
    },
    "AG_SEC_4B": {
        "file": "AG_SEC_4B.dta",
        "variables": [
            "ag4b_10_1",
            "ag4b_10a_1",
            "ag4b_10c_1",
            "ag4b_17",
            "ag4b_19",
            "ag4b_21",
            "ag4b_22",
            "ag4b_25",
            "ag4b_27",
            "ag4b_28",
            "ag4b_29",
        ],
    },
}

for module, config in modules.items():

    print("\n" + "=" * 85)
    print(module)
    print("=" * 85)

    df, meta = pyreadstat.read_dta(
        str(ROOT / config["file"])
    )

    for variable in config["variables"]:

        if variable not in df.columns:
            continue

        series = df[variable]

        print("\nVARIABLE:", variable)
        print("LABEL:", meta.column_names_to_labels.get(variable))
        print("VALUE LABELS:", meta.variable_value_labels.get(variable, {}))
        print("MISSING:", series.isna().sum())
        print("UNIQUE VALUES:", series.nunique())

        if series.nunique() <= 30:
            print("VALUE COUNTS:")
            print(series.value_counts(dropna=False).sort_index().to_string())
        else:
            print("DESCRIPTIVE STATISTICS:")
            print(series.describe().to_string())

print("\nMETADATA INVESTIGATION COMPLETE.")
print("RAW NPS DATA WAS NOT MODIFIED.")
