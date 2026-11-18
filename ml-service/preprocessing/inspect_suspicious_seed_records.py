from pathlib import Path
import pyreadstat

BASE = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

CASES = {
    "AG_SEC_4A.dta": {
        "quantity": "ag4a_10_1",
        "unit": "ag4a_10_2",
        "values": [400, 500],
    },
    "AG_SEC_4B.dta": {
        "quantity": "ag4b_10_1",
        "unit": "ag4b_10_2",
        "values": [1500],
    },
}

for filename, config in CASES.items():
    print("\n" + "=" * 100)
    print("FILE:", filename)
    print("=" * 100)

    df, meta = pyreadstat.read_dta(str(BASE / filename))

    print("\nIDENTIFIER CANDIDATES:")
    for col in df.columns:
        if any(
            word in col.lower()
            for word in ["hh", "house", "plot", "id", "cluster", "ea"]
        ):
            print(
                col,
                "|",
                meta.column_names_to_labels.get(col, "")
            )

    quantity = config["quantity"]
    unit = config["unit"]

    for value in config["values"]:
        selected = df[
            (df["cropid"] == 11)
            & (df[quantity] == value)
        ]

        print("\n" + "-" * 90)
        print("QUANTITY:", value)
        print("MATCHING RECORDS:", len(selected))

        for index, row in selected.iterrows():
            print("\nROW INDEX:", index)

            for col in df.columns:
                val = row[col]
                label = meta.column_names_to_labels.get(col, "")
                print(f"{col}: {val!r} | {label}")

            print("\nUNIT CODE:", row[unit])

    print("\nMODULE INSPECTION COMPLETED.")

print("\nRAW DATA WAS NOT MODIFIED.")
print("NO UNIT CONVERSION WAS PERFORMED.")
print("MODEL TRAINING WAS NOT STARTED.")
