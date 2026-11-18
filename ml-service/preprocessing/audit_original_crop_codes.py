from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = (
    BASE_DIR / "data" / "raw" / "nbs" / "nps2019"
    / "TZA_2019_NPD-SDD_v06_M_STATA12"
)

FILES = {
    "AG_SEC_4A": {
        "file": "AG_SEC_4A.dta",
        "quantity": "ag4a_27",
        "area": "ag4a_21",
        "flag": "ag4a_19",
    },
    "AG_SEC_4B": {
        "file": "AG_SEC_4B.dta",
        "quantity": "ag4b_28",
        "area": "ag4b_21",
        "flag": "ag4b_19",
    },
}

for name, config in FILES.items():

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    path = DATA_DIR / config["file"]

    df = pd.read_stata(
        path,
        convert_categoricals=False
    )

    print("\nRAW CROP CODES:")
    print(df["cropid"].value_counts(dropna=False).sort_index())

    print("\nMAIZE RECORDS (ORIGINAL CODE 11):")

    maize = df[df["cropid"] == 11].copy()

    print("Maize records:", len(maize))

    print("\nMAIZE HARVEST QUANTITY:")
    print(maize[config["quantity"]].describe())

    print("\nMAIZE HARVEST FLAGS:")
    print(maize[config["flag"]].value_counts(dropna=False))

    print("\nMAIZE HARVEST AREA:")
    print(maize[config["area"]].describe())

    print("\nFULL CROP KEY DUPLICATES:")

    duplicate_count = df.duplicated(
        subset=["sdd_hhid", "plotnum", "cropid"],
        keep=False
    ).sum()

    print("Duplicate rows:", duplicate_count)

    print("\nHARVEST QUANTITY BY CROP:")

    summary = (
        df.groupby("cropid")[config["quantity"]]
        .agg(["count", "median", "mean", "max"])
        .sort_values("count", ascending=False)
    )

    print(summary.to_string())

print("\nRAW CODE AUDIT COMPLETED.")
print("Original Stata crop codes preserved.")
print("Raw datasets were not modified.")
print("No model was trained.")
