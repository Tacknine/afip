from pathlib import Path
import pyreadstat

BASE = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

FILES = ["AG_SEC_4A.dta", "AG_SEC_4B.dta"]

for filename in FILES:
    print("\n" + "=" * 90)
    print(filename)
    print("=" * 90)

    df, meta = pyreadstat.read_dta(str(BASE / filename))

    for col in df.columns:
        if any(x in col.lower() for x in ["10_2", "10a_2", "10c_2"]):
            print("\nVARIABLE:", col)
            print("LABEL:", meta.column_names_to_labels.get(col, ""))
            print("VALUE LABELS:")
            print(meta.variable_value_labels.get(col, {}))
            print("DISTRIBUTION:")
            print(df[col].value_counts(dropna=False).sort_index())

    print("\nPOSSIBLE OTHER SPECIFICATION VARIABLES:")

    for col in df.columns:
        label = meta.column_names_to_labels.get(col, "")

        if "specif" in col.lower() or "specif" in label.lower():
            print(col, "|", label)

print("\nUNIT CODE VERIFICATION COMPLETED.")
print("RAW DATA WAS NOT MODIFIED.")
