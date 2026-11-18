from pathlib import Path
import pandas as pd
import pyreadstat

BASE = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

TARGETS = {
    "AG_SEC_4A.dta": {
        "prefix": "ag4a",
        "records": [
            ("0058-001-001", 2),
            ("0300-001-001", 4),
            ("0315-001-001", 2),
            ("0421-001-002", 2),
            ("0437-001-001", 1),
            ("0456-001-001", 2),
            ("0585-001-003", 2),
            ("0666-001-001", 1),
        ],
    },
    "AG_SEC_4B.dta": {
        "prefix": "ag4b",
        "records": [
            ("0136-001-001", 2),
        ],
    },
}

def inspect_file(filename, config):
    prefix = config["prefix"]

    print("\n" + "=" * 110)
    print("FILE:", filename)
    print("=" * 110)

    df, meta = pyreadstat.read_dta(str(BASE / filename))

    # Identify variables belonging to the seed section.
    seed_columns = [
        col for col in df.columns
        if col.startswith(prefix + "_10")
    ]

    # Find other potentially relevant variables using their labels.
    relevant_labels = []

    for col, label in meta.column_names_to_labels.items():
        text = str(label).lower()

        if any(word in text for word in [
            "seed", "source", "purchase",
            "previous", "specify", "other",
        ]):
            relevant_labels.append(col)

    print("\nSEED SECTION VARIABLES:")
    for col in seed_columns:
        print(f"{col}: {meta.column_names_to_labels.get(col, '')}")

    print("\nOTHER POTENTIALLY RELEVANT VARIABLES:")
    for col in relevant_labels:
        if col not in seed_columns:
            print(f"{col}: {meta.column_names_to_labels.get(col, '')}")

    for household, plot in config["records"]:
        match = df[
            (df["sdd_hhid"].astype(str) == household)
            & (pd.to_numeric(df["plotnum"], errors="coerce") == plot)
        ]

        print("\n" + "-" * 100)
        print("HOUSEHOLD:", household, "| PLOT:", plot)
        print("MATCHES:", len(match))

        if match.empty:
            print("RECORD NOT FOUND.")
            continue

        for _, row in match.iterrows():
            print("\nIDENTIFICATION:")
            for col in ["sdd_hhid", "plotnum", "cropid"]:
                print(col, "=", row.get(col))

            print("\nSEED SECTION VALUES:")
            for col in seed_columns:
                print(
                    f"{col} = {row.get(col)}"
                    f" | LABEL: {meta.column_names_to_labels.get(col, '')}"
                )

            print("\nOTHER RELEVANT VALUES:")
            for col in relevant_labels:
                if col not in seed_columns:
                    print(
                        f"{col} = {row.get(col)}"
                        f" | LABEL: {meta.column_names_to_labels.get(col, '')}"
                    )

            print("\nVALUE LABELS FOR SEED VARIABLES:")
            for col in seed_columns:
                label_set = meta.variable_to_label.get(col)

                if label_set:
                    print(
                        col,
                        meta.value_labels.get(label_set, {})
                    )


for filename, config in TARGETS.items():
    inspect_file(filename, config)

print("\nRECORD-LEVEL SEED INVESTIGATION COMPLETED.")
print("RAW DATA WAS NOT MODIFIED.")
print("NO UNIT CONVERSION WAS PERFORMED.")
print("NO CLEANING WAS PERFORMED.")
print("MODEL TRAINING WAS NOT STARTED.")
