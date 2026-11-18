
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "nbs"
    / "nps2019"
    / "TZA_2019_NPD-SDD_v06_M_STATA12"
)

DATASETS = {
    "AG_SEC_4A": {
        "file": "AG_SEC_4A.dta",
        "prefix": "ag4a",
        "harvest_quantity": "ag4a_27",
        "harvest_area": "ag4a_21",
        "harvest_flag": "ag4a_19",
        "seed_quantity": "ag4a_10_1",
        "seed_unit": "ag4a_10_2",
    },
    "AG_SEC_4B": {
        "file": "AG_SEC_4B.dta",
        "prefix": "ag4b",
        "harvest_quantity": "ag4b_28",
        "harvest_area": "ag4b_21",
        "harvest_flag": "ag4b_19",
        "seed_quantity": "ag4b_10_1",
        "seed_unit": "ag4b_10_2",
    },
}


def print_value_labels(file_path):
    print("\nSTATA VALUE LABEL SETS")

    reader = pd.io.stata.StataReader(file_path)

    try:
        labels = reader.value_labels()

        if not labels:
            print("No value label sets found.")
            return

        for label_name, mapping in labels.items():
            print(f"\nLABEL SET: {label_name}")

            for code, description in mapping.items():
                print(f"{code}: {description}")

    finally:
        reader.close()


def audit_dataset(name, config):

    file_path = DATA_DIR / config["file"]

    print("\n" + "=" * 90)
    print(f"DATASET: {name}")
    print("=" * 90)

    df = pd.read_stata(file_path)

    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    # --------------------------------------------------------
    # CROP CODE DISTRIBUTION
    # --------------------------------------------------------

    print("\nCROP CODE DISTRIBUTION:")

    print(
        df["cropid"]
        .value_counts(dropna=False)
        .sort_index()
        .to_string()
    )

    # --------------------------------------------------------
    # DUPLICATE KEY AUDIT
    # --------------------------------------------------------

    keys = ["sdd_hhid", "plotnum", "cropid"]

    print("\nFULL CROP KEY AUDIT:")

    duplicate_count = df.duplicated(
        subset=keys,
        keep=False
    ).sum()

    print("Duplicate rows:", duplicate_count)

    # --------------------------------------------------------
    # HARVEST QUANTITY
    # --------------------------------------------------------

    quantity = config["harvest_quantity"]

    print("\nHARVEST QUANTITY AUDIT:")
    print("Variable:", quantity)

    print("Variable label:")
    print(df.attrs.get("variable_labels", {}).get(quantity))

    if quantity in df.columns:

        print("\nDescriptive statistics:")
        print(df[quantity].describe().to_string())

        print("\nZero values:", (df[quantity] == 0).sum())
        print("Negative values:", (df[quantity] < 0).sum())
        print("Missing values:", df[quantity].isna().sum())

    # --------------------------------------------------------
    # HARVEST AREA
    # --------------------------------------------------------

    area = config["harvest_area"]

    print("\nHARVEST AREA AUDIT:")
    print("Variable:", area)

    print("Descriptive statistics:")
    print(df[area].describe().to_string())

    print("Missing:", df[area].isna().sum())
    print("Zero:", (df[area] == 0).sum())
    print("Negative:", (df[area] < 0).sum())

    # --------------------------------------------------------
    # HARVEST FLAG
    # --------------------------------------------------------

    flag = config["harvest_flag"]

    print("\nHARVEST FLAG DISTRIBUTION:")
    print(df[flag].value_counts(dropna=False).to_string())

    # --------------------------------------------------------
    # SEED UNIT
    # --------------------------------------------------------

    unit = config["seed_unit"]

    print("\nSEED UNIT DISTRIBUTION:")
    print(df[unit].value_counts(dropna=False).to_string())

    print("\nMAIZE HARVEST SUMMARY:")

    maize = df[df["cropid"] == 11].copy()

    print("Maize records:", len(maize))

    if len(maize) > 0:

        print("\nMaize harvest quantity:")
        print(maize[quantity].describe().to_string())

        print("\nMaize harvest flag:")
        print(maize[flag].value_counts(dropna=False).to_string())

        print("\nMaize seed units:")
        print(maize[unit].value_counts(dropna=False).to_string())

    # --------------------------------------------------------
    # VALUE LABELS
    # --------------------------------------------------------

    print_value_labels(file_path)


def main():

    print("=" * 90)
    print("AFIP - CROP CODE AND HARVEST QUALITY AUDIT")
    print("READ ONLY - NO RAW DATA MODIFICATION - NO TRAINING")
    print("=" * 90)

    for name, config in DATASETS.items():
        audit_dataset(name, config)

    print("\n" + "=" * 90)
    print("CROP CODE AND HARVEST AUDIT COMPLETED")
    print("RAW DATA WAS NOT MODIFIED.")
    print("NO UNIT CONVERSION WAS ASSUMED.")
    print("NO MODEL WAS TRAINED.")
    print("=" * 90)


if __name__ == "__main__":
    main()
