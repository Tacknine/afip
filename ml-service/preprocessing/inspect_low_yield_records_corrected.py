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
print("AFIP - CORRECTED LOW YIELD INVESTIGATION")
print("=" * 80)

print("Low yield observations:", len(low))

for module, filename, month_begin, month_end in [
    ("AG_SEC_4A", "AG_SEC_4A.dta", "ag4a_24_1", "ag4a_24_2"),
    ("AG_SEC_4B", "AG_SEC_4B.dta", "ag4b_24_1", "ag4b_24_2"),
]:

    subset = low[low["source_module"] == module].copy()

    if subset.empty:
        continue

    print("\n" + "=" * 80)
    print("MODULE:", module)
    print("=" * 80)

    df, meta = pyreadstat.read_dta(str(ROOT / filename))

    # Correct matching: household + plot + crop
    merged = subset.merge(
        df,
        left_on=[
            "household_id",
            "plot_number",
            "crop_code"
        ],
        right_on=[
            "sdd_hhid",
            "plotnum",
            "cropid"
        ],
        how="left",
        validate="one_to_one",
        indicator=True,
        suffixes=("_audit", "_raw")
    )

    print("Audit observations:", len(subset))
    print("Matched observations:", (merged["_merge"] == "both").sum())
    print("Unmatched observations:", (merged["_merge"] != "both").sum())

    columns = [
        "household_id",
        "plot_number",
        "crop_code",
        "season",
        "area_harvested_acres",
        "quantity_reported",
        "yield_kg_per_hectare",
        "ag4a_17" if module == "AG_SEC_4A" else "ag4b_17",
        "ag4a_22" if module == "AG_SEC_4A" else "ag4b_22",
        month_begin,
        month_end,
    ]

    if module == "AG_SEC_4B":
        columns.append("ag4b_25")

    columns = [c for c in columns if c in merged.columns]

    print("\nCORRECTLY MATCHED MAIZE RECORDS:")
    print(merged[columns].to_string(index=False))

    print("\nMONTH VALUE LABELS:")

    for variable in [month_begin, month_end]:

        labels = meta.variable_value_labels.get(variable, {})

        print(variable, labels)

    print("\nAREA AND QUANTITY CROSS-CHECK:")

    for _, row in merged.iterrows():

        area_var = "ag4a_21" if module == "AG_SEC_4A" else "ag4b_21"
        quantity_var = "ag4a_27" if module == "AG_SEC_4A" else "ag4b_28"

        print(
            row["household_id"],
            "plot:", row["plot_number"],
            "area audit/raw:",
            row["area_harvested_acres"],
            row[area_var],
            "quantity audit/raw:",
            row["quantity_reported"],
            row[quantity_var]
        )

print("\nCORRECTED LOW YIELD INVESTIGATION COMPLETE.")
print("RAW NPS DATA WAS NOT MODIFIED.")
