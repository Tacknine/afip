from pathlib import Path
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

files = [
    "AG_SEC_4A.dta",
    "AG_SEC_4B.dta"
]

for filename in files:

    df, meta = pyreadstat.read_dta(
        str(ROOT / filename)
    )

    print("\n" + "=" * 80)
    print(filename)
    print("=" * 80)

    for variable, label in zip(
        meta.column_names,
        meta.column_labels
    ):

        text = f"{variable} {label}".lower()

        if any(word in text for word in [
            "crop",
            "code",
            "grown",
            "cultivated"
        ]):

            print("\nVARIABLE:", variable)
            print("LABEL:", label)

            label_set = meta.variable_to_label.get(variable)

            if label_set:
                print(
                    "VALUE LABELS:",
                    meta.value_labels.get(label_set, {})
                )

            if variable in df.columns:
                print(
                    "OBSERVED VALUES:",
                    df[variable].value_counts(
                        dropna=False
                    ).head(30).to_dict()
                )

print("\nCROP VARIABLE INSPECTION COMPLETE.")
