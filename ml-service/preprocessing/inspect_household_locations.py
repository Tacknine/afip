from pathlib import Path
import pyreadstat

ROOT = Path("data/raw/nbs/nps2019/TZA_2019_NPD-SDD_v06_M_STATA12")

files = list(ROOT.glob("HH_SEC_A*.dta"))

if not files:
    raise FileNotFoundError("HH_SEC_A dataset haijapatikana.")

for file in files:
    df, meta = pyreadstat.read_dta(str(file))

    print("\n" + "=" * 65)
    print("FILE:", file.name)
    print("TOTAL ROWS:", len(df))
    print("TOTAL COLUMNS:", len(df.columns))

    print("\nPOSSIBLE HOUSEHOLD IDENTIFIERS:")
    for col in df.columns:
        if any(x in col.lower() for x in ["hhid", "key", "household"]):
            print(col, ":", meta.column_names_to_labels.get(col))

    print("\nLOCATION VARIABLES:")
    for col in df.columns:
        if any(x in col.lower() for x in [
            "region", "district", "ward", "village", "location"
        ]):
            print(
                col,
                "=>",
                meta.column_names_to_labels.get(col),
                "| UNIQUE:",
                df[col].nunique(),
                "| MISSING:",
                df[col].isna().sum()
            )

    print("\nSAMPLE:")
    selected = [
        c for c in df.columns
        if any(x in c.lower() for x in [
            "hhid", "key", "region", "district", "ward", "village"
        ])
    ]

    print(df[selected].head(10).to_string(index=False))
