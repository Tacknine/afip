from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = (
    BASE_DIR / "data" / "raw" / "nbs" / "nps2019"
    / "TZA_2019_NPD-SDD_v06_M_STATA12"
)

FILES = {
    "AG_SEC_4A": [
        "ag4a_19", "ag4a_20", "ag4a_21",
        "ag4a_22", "ag4a_23", "ag4a_24_1",
        "ag4a_24_2", "ag4a_25", "ag4a_26",
        "ag4a_27", "ag4a_28"
    ],
    "AG_SEC_4B": [
        "ag4b_19", "ag4b_20", "ag4b_21",
        "ag4b_22", "ag4b_23", "ag4b_24_1",
        "ag4b_24_2", "ag4b_25", "ag4b_26",
        "ag4b_27", "ag4b_28", "ag4b_29"
    ]
}

for dataset, variables in FILES.items():

    path = DATA_DIR / f"{dataset}.dta"

    print("\n" + "=" * 90)
    print(dataset)
    print("=" * 90)

    with pd.io.stata.StataReader(path) as reader:
        variable_labels = reader.variable_labels()
        value_labels = reader.value_labels()

    for variable in variables:

        print("\nVARIABLE:", variable)
        print("LABEL:", variable_labels.get(variable, "NOT FOUND"))

        if variable in value_labels:
            print("VALUE LABELS:")
            print(value_labels[variable])

    # Show the original data for the largest maize quantities.
    df = pd.read_stata(path, convert_categoricals=False)

    quantity = (
        "ag4a_27" if dataset == "AG_SEC_4A"
        else "ag4b_28"
    )

    area = (
        "ag4a_21" if dataset == "AG_SEC_4A"
        else "ag4b_21"
    )

    flag = (
        "ag4a_19" if dataset == "AG_SEC_4A"
        else "ag4b_19"
    )

    maize = df[df["cropid"] == 11].copy()

    print("\nTOP 15 MAIZE HARVEST QUANTITIES:")

    columns = [
        "sdd_hhid", "plotnum", "cropid",
        quantity, area, flag
    ]

    print(
        maize[columns]
        .sort_values(quantity, ascending=False)
        .head(15)
        .to_string(index=False)
    )

print("\nHARVEST METADATA AUDIT COMPLETED.")
print("RAW DATA WAS NOT MODIFIED.")
print("NO UNIT CONVERSION WAS ASSUMED.")
print("NO MODEL WAS TRAINED.")
