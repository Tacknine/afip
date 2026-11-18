from pathlib import Path
import pandas as pd
import pyreadstat

BASE = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

MODULES = {
    "AG_SEC_4A.dta": [
        "ag4a_01", "ag4a_02", "ag4a_04", "ag4a_05",
        "ag4a_06", "ag4a_08",
        "ag4a_10_1", "ag4a_10_2",
        "ag4a_10a_1", "ag4a_10a_2", "ag4a_10b",
        "ag4a_10c_1", "ag4a_10c_2",
        "ag4a_12", "ag4a_13_1",
        "ag4a_19", "ag4a_21", "ag4a_27", "ag4a_28",
    ],
    "AG_SEC_4B.dta": [
        "ag4b_01", "ag4b_02", "ag4b_04", "ag4b_05",
        "ag4b_06", "ag4b_08",
        "ag4b_10_1", "ag4b_10_2",
        "ag4b_10a_1", "ag4b_10a_2", "ag4b_10b",
        "ag4b_10c_1", "ag4b_10c_2",
        "ag4b_12", "ag4b_13_1",
        "ag4b_19", "ag4b_21", "ag4b_28", "ag4b_29",
    ],
}

print("=" * 100)
print("AFIP - MAIZE FEATURE VALUE AND METADATA AUDIT")
print("=" * 100)

for filename, variables in MODULES.items():
    path = BASE / filename

    print("\n" + "=" * 100)
    print("MODULE:", filename)
    print("=" * 100)

    if not path.exists():
        print("FILE NOT FOUND:", path)
        continue

    df, meta = pyreadstat.read_dta(str(path))

    maize = df[df["cropid"] == 11].copy()

    print("TOTAL ROWS:", len(df))
    print("MAIZE ROWS:", len(maize))

    for var in variables:
        if var not in maize.columns:
            print("\nVARIABLE NOT FOUND:", var)
            continue

        label = meta.column_names_to_labels.get(var, "")
        series = maize[var]

        print("\n" + "-" * 90)
        print("VARIABLE:", var)
        print("LABEL:", label)
        print("DATA TYPE:", series.dtype)
        print("MISSING:", series.isna().sum())
        print("UNIQUE:", series.nunique(dropna=True))

        label_set = meta.variable_to_label.get(var)
        value_labels = (
            meta.value_labels.get(label_set, {})
            if label_set else {}
        )

        if value_labels:
            print("VALUE LABELS:")
            for code, meaning in value_labels.items():
                print(f"  {code!r} = {meaning}")

        print("OBSERVED VALUES:")
        counts = series.value_counts(dropna=False).head(20)

        for value, count in counts.items():
            meaning = value_labels.get(value, "")
            print(
                f"  {value!r}: {count}"
                + (f" | {meaning}" if meaning else "")
            )

print("\n" + "=" * 100)
print("FEATURE VALUE AUDIT COMPLETED.")
print("RAW DATA WAS NOT MODIFIED.")
print("MODEL TRAINING WAS NOT STARTED.")
print("=" * 100)
