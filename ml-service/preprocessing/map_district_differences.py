from pathlib import Path
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

_, meta = pyreadstat.read_dta(
    str(ROOT / "HH_SEC_A.dta")
)

def get_labels(variable):
    label_set = meta.variable_to_label.get(variable)
    if not label_set:
        return {}
    return meta.value_labels.get(label_set, {})

t0_labels = get_labels("t0_district")
current_labels = get_labels("hh_a02_1")

differences = [
    (186, 182, 2),
    (174, 176, 2),
    (53, 56, 1),
    (51, 57, 1),
    (46, 410, 1),
    (71, 62, 1),
    (55, 52, 1),
    (147, 197, 1),
    (91, 99, 1),
    (188, 187, 1),
    (207, 203, 1),
    (251, 256, 1),
    (253, 176, 1),
]

print("\nT0 DISTRICT QUESTION:")
print(meta.column_labels[meta.column_names.index("t0_district")])

print("\nCURRENT DISTRICT QUESTION:")
print(meta.column_labels[meta.column_names.index("hh_a02_1")])

print("\nDISTRICT DIFFERENCES")
print("-" * 90)

for old_code, new_code, count in differences:
    old_name = t0_labels.get(old_code, "UNKNOWN")
    new_name = current_labels.get(new_code, "UNKNOWN")

    print(
        f"T0: {old_code} - {old_name} | "
        f"CURRENT: {new_code} - {new_name} | "
        f"RECORDS: {count}"
    )

print("\nAUDIT COMPLETE.")
