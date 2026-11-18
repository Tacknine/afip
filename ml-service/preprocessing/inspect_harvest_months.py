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
        "end": "ag4a_24_2"
    },
    "AG_SEC_4B": {
        "file": "AG_SEC_4B.dta",
        "begin": "ag4b_24_1",
        "end": "ag4b_24_2"
    }
}

for name, config in files.items():
    df, meta = pyreadstat.read_dta(
        str(ROOT / config["file"])
    )

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    for variable in [config["begin"], config["end"]]:
        if variable not in df.columns:
            print(variable, "NOT FOUND")
            continue

        print("\nVARIABLE:", variable)
        print(
            "QUESTION:",
            meta.column_labels[meta.column_names.index(variable)]
        )

        label_set = meta.variable_to_label.get(variable)

        if label_set:
            print(
                "VALUE LABELS:",
                meta.value_labels.get(label_set, {})
            )

        print("OBSERVED VALUES:")
        print(df[variable].value_counts(dropna=False).sort_index())

print("\nAUDIT COMPLETE.")
