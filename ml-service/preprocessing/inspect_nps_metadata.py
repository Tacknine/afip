from pathlib import Path
import pyreadstat

root = Path("data/raw/nbs/nps2019/TZA_2019_NPD-SDD_v06_M_STATA12")

for filename in ["AG_SEC_4A.dta", "AG_SEC_4B.dta"]:
    path = root / filename
    df, meta = pyreadstat.read_dta(str(path))

    print("\n==========", filename, "==========")

    print("\nCROP VARIABLE LABEL:")
    print(meta.column_names_to_labels.get("cropid"))

    print("\nVARIABLE TO LABEL:")
    print(meta.variable_to_label.get("cropid"))

    print("\nALL VALUE LABEL SETS:")
    for name, labels in meta.value_labels.items():
        print("\nLABEL SET:", name)
        print(labels)

    print("\nCROP IDS:")
    print(sorted(df["cropid"].dropna().unique().tolist()))
