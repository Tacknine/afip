from pathlib import Path
import pandas as pd

BASE = Path(
    "data/raw/nbs/nps2019/TZA_2019_NPD-SDD_v06_M_STATA12"
)
OUT = Path("reports")
OUT.mkdir(exist_ok=True)

FILES = [
    "AG_SEC_3A.dta",
    "AG_SEC_3B.dta",
    "AG_SEC_4A.dta",
    "AG_SEC_4B.dta",
    "AG_SEC_6A.dta",
    "AG_SEC_6B.dta",
]

KEYS = ["sdd_hhid", "plotnum"]

TARGETS = {
    "AG_SEC_4A.dta": [
        "cropid", "ag4a_01", "ag4a_02", "ag4a_04",
        "ag4a_06", "ag4a_08", "ag4a_10_1",
        "ag4a_10_2", "ag4a_17", "ag4a_19",
        "ag4a_21", "ag4a_27", "ag4a_28"
    ],
    "AG_SEC_4B.dta": [
        "cropid", "ag4b_01", "ag4b_02", "ag4b_04",
        "ag4b_06", "ag4b_08", "ag4b_10_1",
        "ag4b_10_2", "ag4b_17", "ag4b_19",
        "ag4b_21", "ag4b_28", "ag4b_29"
    ],
    "AG_SEC_3A.dta": [
        "ag3a_03", "ag3a_07", "ag3a_10",
        "ag3a_11", "ag3a_13", "ag3a_17",
        "ag3a_18", "ag3a_19", "ag3a_21",
        "ag3a_40", "ag3a_41", "ag3a_42",
        "ag3a_47", "ag3a_48", "ag3a_49",
        "ag3a_54", "ag3a_55", "ag3a_56"
    ],
    "AG_SEC_3B.dta": [
        "ag3b_03", "ag3b_07", "ag3b_10",
        "ag3b_11", "ag3b_13", "ag3b_17",
        "ag3b_18", "ag3b_19", "ag3b_21",
        "ag3b_40", "ag3b_41", "ag3b_42",
        "ag3b_47", "ag3b_48", "ag3b_49",
        "ag3b_54", "ag3b_55", "ag3b_56"
    ],
    "AG_SEC_6A.dta": [
        "cropid", "ag6a_02", "ag6a_03",
        "ag6a_04", "ag6a_09"
    ],
    "AG_SEC_6B.dta": [
        "cropid", "ag6b_02", "ag6b_03",
        "ag6b_04", "ag6b_09"
    ]
}

frames = {}

print("=" * 100)
print("AFIP TARGET AND FEATURE VALIDATION")
print("READ ONLY - NO CLEANING - NO TRAINING")
print("=" * 100)

for filename in FILES:
    path = BASE / filename

    print("\n" + "=" * 100)
    print("FILE:", filename)

    if not path.exists():
        print("FILE NOT FOUND")
        continue

    reader = pd.read_stata(
        path,
        iterator=True,
        convert_categoricals=False
    )
    df = reader.read()
    labels = reader.variable_labels()
    value_labels = reader.value_labels()

    frames[filename] = df

    print("ROWS:", len(df))
    print("COLUMNS:", len(df.columns))

    key_cols = [c for c in KEYS if c in df.columns]

    if key_cols:
        print("\nKEY DUPLICATE AUDIT:", key_cols)
        print("Duplicate rows:", int(df.duplicated(key_cols).sum()))

    selected = TARGETS.get(filename, [])

    print("\nSELECTED VARIABLE AUDIT")

    for col in selected:
        if col not in df.columns:
            print(f"\n{col}: NOT FOUND")
            continue

        s = df[col]
        print("\nVARIABLE:", col)
        print("QUESTION:", labels.get(col, "No label"))
        print("TYPE:", s.dtype)
        print("MISSING:", int(s.isna().sum()))
        print("UNIQUE:", int(s.nunique(dropna=True)))

        if s.nunique(dropna=True) <= 20:
            print("VALUE COUNTS:")
            print(s.value_counts(dropna=False).head(20).to_string())

        if pd.api.types.is_numeric_dtype(s):
            print("NUMERIC SUMMARY:")
            print(s.describe().to_string())

        if col in value_labels:
            print("VALUE LABELS:")
            print(value_labels[col])

    if filename in ["AG_SEC_4A.dta", "AG_SEC_4B.dta"]:
        print("\nCOMPLETE HARVEST AND SEED QUESTION LABELS")

        for col in df.columns:
            label = str(labels.get(col, ""))
            if any(word in label.lower() for word in [
                "harvest", "seed", "planted", "crop",
                "fraction", "loss"
            ]):
                print(f"{col}: {label}")

print("\n" + "=" * 100)
print("CROSS-DATASET KEY OVERLAP AUDIT")
print("=" * 100)

for season in ["A", "B"]:
    plot_file = f"AG_SEC_3{season}.dta"
    crop_file = f"AG_SEC_4{season}.dta"

    if plot_file not in frames or crop_file not in frames:
        continue

    plot_df = frames[plot_file]
    crop_df = frames[crop_file]

    keys = ["sdd_hhid", "plotnum"]

    plot_keys = plot_df[keys].drop_duplicates()
    crop_keys = crop_df[keys].drop_duplicates()

    overlap = plot_keys.merge(
        crop_keys,
        on=keys,
        how="inner"
    )

    print(f"\n{plot_file} vs {crop_file}")
    print("Unique plot keys in plot data:", len(plot_keys))
    print("Unique plot keys in crop data:", len(crop_keys))
    print("Matching plot keys:", len(overlap))
    print("Crop records:", len(crop_df))
    print("Crop records with missing key:",
          int(crop_df[keys].isna().any(axis=1).sum()))

print("\n" + "=" * 100)
print("VALIDATION AUDIT COMPLETED")
print("RAW DATA WAS NOT MODIFIED")
print("NO UNIT CONVERSION WAS ASSUMED")
print("NO MODEL WAS TRAINED")
print("=" * 100)
