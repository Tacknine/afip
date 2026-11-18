from pathlib import Path
import pandas as pd
import pyreadstat

BASE = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

FILES = ["AG_SEC_4A.dta", "AG_SEC_4B.dta"]

for filename in FILES:
    print("\n" + "=" * 100)
    print(filename)
    print("=" * 100)

    df, meta = pyreadstat.read_dta(str(BASE / filename))

    print("\n1. ALL SEED-RELATED VARIABLES")

    for col in df.columns:
        label = meta.column_names_to_labels.get(col, "")

        if any(word in col.lower() + " " + label.lower()
               for word in ["seed", "specify", "specification"]):
            print(f"{col:25} | {label}")

    print("\n2. VARIABLES AROUND SEED QUESTIONS")

    for col in df.columns:
        if "10" in col.lower() or col.endswith("_12"):
            print(
                col,
                "|",
                meta.column_names_to_labels.get(col, "")
            )

    prefixes = ["ag4a"] if "4A" in filename else ["ag4b"]

    for prefix in prefixes:
        quantity_vars = {
            "total": f"{prefix}_10_1",
            "previous": f"{prefix}_10a_1",
            "purchased": f"{prefix}_10c_1",
        }

        unit_vars = {
            "total": f"{prefix}_10_2",
            "previous": f"{prefix}_10a_2",
            "purchased": f"{prefix}_10c_2",
        }

        print("\n3. QUANTITY AND UNIT COMPLETENESS")

        for name in quantity_vars:
            q = quantity_vars[name]
            u = unit_vars[name]

            temp = df[[q, u]].copy()

            print("\nCOMPONENT:", name)
            print("Quantity variable:", q)
            print("Unit variable:", u)

            print("Quantity missing:", temp[q].isna().sum())
            print("Unit missing:", temp[u].isna().sum())

            print("QUANTITY/UNIT COMBINATIONS:")

            print(
                pd.crosstab(
                    temp[q].isna().map(
                        {True: "MISSING", False: "PRESENT"}
                    ),
                    temp[u].isna().map(
                        {True: "MISSING", False: "PRESENT"}
                    ),
                    margins=True
                )
            )

            print("\nPOSITIVE QUANTITY WITH MISSING UNIT:")

            suspicious = temp[
                (temp[q] > 0) & temp[u].isna()
            ]

            print("Count:", len(suspicious))
            print(suspicious.head(20))

            print("\nZERO QUANTITY WITH MISSING UNIT:")

            zero_missing = temp[
                (temp[q] == 0) & temp[u].isna()
            ]

            print("Count:", len(zero_missing))

    print("\n4. OTHER UNIT RECORDS")

    total_q = f"{prefix}_10_1"
    total_u = f"{prefix}_10_2"

    other = df[df[total_u] == 5]

    print("Total OTHER records:", len(other))

    display_cols = [
        col for col in [
            "sdd_hhid",
            "plotnum",
            "cropid",
            total_q,
            total_u,
        ] if col in df.columns
    ]

    print(other[display_cols].to_string(index=False))

print("\nSEED QUESTIONNAIRE STRUCTURE AUDIT COMPLETED.")
print("RAW DATA WAS NOT MODIFIED.")
print("NO UNIT CONVERSION WAS PERFORMED.")
print("NO CLEANING WAS PERFORMED.")
print("MODEL TRAINING WAS NOT STARTED.")
