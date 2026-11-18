from pathlib import Path
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

_, meta = pyreadstat.read_dta(
    str(ROOT / "HH_SEC_A.dta")
)

variables = [
    "t0_region",
    "t0_district",
    "t0_ward_code",
    "hh_a01_1",
    "hh_a02_1"
]

print("=" * 65)
print("LOCATION VARIABLE LABEL AUDIT")
print("=" * 65)

for variable in variables:
    print(f"\nVARIABLE: {variable}")

    if variable in meta.column_names:
        index = meta.column_names.index(variable)

        print(
            "QUESTION:",
            meta.column_labels[index]
        )

        label_set = meta.variable_to_label.get(variable)

        print("VALUE LABEL SET:", label_set)

        if label_set:
            labels = meta.value_labels.get(label_set, {})
            print("VALUE LABELS:")
            for code, name in labels.items():
                print(f"  {code}: {name}")
        else:
            print("No value labels available.")
    else:
        print("VARIABLE NOT FOUND")

print("\nAUDIT COMPLETE.")
