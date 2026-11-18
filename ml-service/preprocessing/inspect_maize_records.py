from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path("data/raw/nbs/nps2019/TZA_2019_NPD-SDD_v06_M_STATA12")

FILES = [
    {
        "file": "AG_SEC_4A.dta",
        "season": "Long rainy season 2018",
        "area": "ag4a_21",
        "quantity": "ag4a_27",
    },
    {
        "file": "AG_SEC_4B.dta",
        "season": "Second season",
        "area": "ag4b_21",
        "quantity": "ag4b_28",
    },
]

for item in FILES:
    path = ROOT / item["file"]
    df, meta = pyreadstat.read_dta(str(path))

    print("\n" + "=" * 65)
    print("FILE:", item["file"])
    print("SEASON:", item["season"])
    print("TOTAL RECORDS:", len(df))

    # Crop code 11 = Maize
    maize = df[df["cropid"] == 11].copy()

    print("MAIZE RECORDS:", len(maize))
    print("UNIQUE HOUSEHOLDS:", maize["sdd_hhid"].nunique())
    print("UNIQUE PLOTS:", maize[["sdd_hhid", "plotnum"]].drop_duplicates().shape[0])

    area = item["area"]
    quantity = item["quantity"]

    for col in [area, quantity]:
        maize[col] = pd.to_numeric(maize[col], errors="coerce")

        print(f"\n{col} SUMMARY:")
        print(maize[col].describe().to_string())
        print("MISSING:", maize[col].isna().sum())
        print("ZERO:", (maize[col] == 0).sum())
        print("NEGATIVE:", (maize[col] < 0).sum())

    print("\nSAMPLE RECORDS:")
    columns = ["sdd_hhid", "plotnum", "cropid", area, quantity]
    print(maize[columns].head(15).to_string(index=False))

    print("\nVARIABLE LABELS:")
    for col in [area, quantity]:
        print(col, ":", meta.column_names_to_labels.get(col))

