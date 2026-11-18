from pathlib import Path
import pandas as pd
import pyreadstat

AUDIT = Path("data/processed/maize_yield_audit.csv")

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

audit = pd.read_csv(AUDIT)

low = audit[
    audit["yield_review_status"] == "LOW_YIELD_REVIEW"
].copy()

print("=" * 80)
print("AFIP - LOW YIELD RECORD INVESTIGATION")
print("=" * 80)

print("Records to investigate:", len(low))

for module, filename in [
    ("AG_SEC_4A", "AG_SEC_4A.dta"),
    ("AG_SEC_4B", "AG_SEC_4B.dta"),
]:

    subset = low[low["source_module"] == module]

    if subset.empty:
        continue

    print("\n" + "=" * 80)
    print("MODULE:", module)
    print("=" * 80)

    df, meta = pyreadstat.read_dta(str(ROOT / filename))

    # Find potentially useful variables from their labels.
    keywords = [
        "harvest",
        "area",
        "quantity",
        "month",
        "fraction",
        "remain",
        "days",
        "value",
        "finished",
    ]

    selected = []

    for variable, label in zip(
        meta.column_names,
        meta.column_labels
    ):

        label_text = str(label).lower()

        if any(word in label_text for word in keywords):
            selected.append(variable)

    # Always include identifiers and core measurements.
    required = [
        "sdd_hhid",
        "plotnum",
        "cropid",
    ]

    for variable in required:
        if variable in df.columns and variable not in selected:
            selected.insert(0, variable)

    # Match records using household and plot identifiers.
    merged = subset.merge(
        df,
        left_on=["household_id", "plot_number"],
        right_on=["sdd_hhid", "plotnum"],
        how="left",
        suffixes=("_audit", "_raw")
    )

    print("\nVARIABLE LABELS:")
    for variable in selected:
        if variable in df.columns:
            index = meta.column_names.index(variable)
            print(variable, ":", meta.column_labels[index])

    print("\nLOW YIELD RECORD DETAILS:")

    display_columns = [
        "household_id",
        "plot_number",
        "season",
        "area_harvested_acres",
        "quantity_reported",
        "yield_kg_per_hectare",
    ]

    for variable in selected:
        if variable in merged.columns and variable not in display_columns:
            display_columns.append(variable)

    display_columns = [
        col for col in display_columns
        if col in merged.columns
    ]

    print(
        merged[display_columns]
        .to_string(index=False)
    )

print("\nLOW YIELD INVESTIGATION COMPLETE.")
print("RAW NPS DATA WAS NOT MODIFIED.")
