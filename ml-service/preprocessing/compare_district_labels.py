from pathlib import Path
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

_, meta = pyreadstat.read_dta(
    str(ROOT / "HH_SEC_A.dta")
)

for variable in ["t0_district", "hh_a02_1"]:
    print("\n" + "=" * 60)
    print("VARIABLE:", variable)
    print("=" * 60)

    if variable not in meta.column_names:
        print("VARIABLE NOT FOUND")
        continue

    index = meta.column_names.index(variable)
    print("QUESTION:", meta.column_labels[index])

    label_set = meta.variable_to_label.get(variable)

    if not label_set:
        print("NO VALUE LABELS")
        continue

    labels = meta.value_labels.get(label_set, {})

    for code, name in labels.items():
        print(f"{code}: {name}")

print("\nAUDIT COMPLETE.")
