from pathlib import Path
import pandas as pd
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

AUDIT_FILE = Path("data/processed/maize_yield_audit.csv")
OUTPUT_FILE = Path("data/processed/maize_quantity_value_review.csv")

MODULES = [
    {
        "module": "AG_SEC_4A",
        "file": "AG_SEC_4A.dta",
        "harvested": "ag4a_19",
        "area": "ag4a_21",
        "quantity": "ag4a_27",
        "value": "ag4a_28",
    },
    {
        "module": "AG_SEC_4B",
        "file": "AG_SEC_4B.dta",
        "harvested": "ag4b_19",
        "area": "ag4b_21",
        "quantity": "ag4b_28",
        "value": "ag4b_29",
    },
]

results = []

print("=" * 90)
print("AFIP - MAIZE QUANTITY AND ESTIMATED VALUE VERIFICATION")
print("=" * 90)
print("Crop code: 11 (MAIZE)")
print("Raw data will only be read, never modified.")

for config in MODULES:

    module = config["module"]
    df, meta = pyreadstat.read_dta(str(ROOT / config["file"]))

    required = [
        "sdd_hhid", "plotnum", "cropid",
        config["harvested"], config["area"],
        config["quantity"], config["value"]
    ]

    missing_columns = [c for c in required if c not in df.columns]

    if missing_columns:
        print(f"\nERROR: {module} missing columns: {missing_columns}")
        continue

    maize = df[df["cropid"] == 11].copy()

    maize["source_module"] = module
    maize["household_id"] = maize["sdd_hhid"].astype(str)
    maize["plot_number"] = maize["plotnum"]
    maize["crop_code"] = maize["cropid"]
    maize["harvested"] = maize[config["harvested"]]
    maize["area_harvested_acres"] = maize[config["area"]]
    maize["quantity_reported"] = maize[config["quantity"]]
    maize["estimated_value_reported"] = maize[config["value"]]

    harvested = maize[maize["harvested"] == 1].copy()

    print("\n" + "=" * 90)
    print("MODULE:", module)
    print("=" * 90)

    print("All maize records:", len(maize))
    print("Harvested maize records:", len(harvested))
    print("Not harvested:", (maize["harvested"] == 2).sum())

    print("\nMISSING VALUES - HARVESTED MAIZE")
    print("Missing area:", harvested["area_harvested_acres"].isna().sum())
    print("Missing quantity:", harvested["quantity_reported"].isna().sum())
    print("Missing estimated value:", harvested["estimated_value_reported"].isna().sum())

    print("\nQUANTITY DESCRIPTIVE STATISTICS")
    print(harvested["quantity_reported"].describe())

    print("\nESTIMATED VALUE DESCRIPTIVE STATISTICS")
    print(harvested["estimated_value_reported"].describe())

    valid = harvested[
        harvested["quantity_reported"].notna()
        & harvested["estimated_value_reported"].notna()
        & (harvested["quantity_reported"] > 0)
        & (harvested["estimated_value_reported"] > 0)
    ].copy()

    valid["value_per_reported_quantity_unit"] = (
        valid["estimated_value_reported"] / valid["quantity_reported"]
    )

    print("\nVALID QUANTITY-VALUE PAIRS:", len(valid))
    print("\nVALUE / REPORTED QUANTITY RATIO")
    print(valid["value_per_reported_quantity_unit"].describe())

    print("\nLOW QUANTITY BUT HIGH REPORTED VALUE")
    suspicious = valid[
        (valid["quantity_reported"] <= 10)
    ].sort_values("value_per_reported_quantity_unit", ascending=False)

    display_columns = [
        "sdd_hhid", "plotnum",
        "area_harvested_acres",
        "quantity_reported",
        "estimated_value_reported",
        "value_per_reported_quantity_unit"
    ]

    if suspicious.empty:
        print("No records with quantity <= 10 and positive value.")
    else:
        print(suspicious[display_columns].head(30).to_string(index=False))

    print("\nZERO OR NEGATIVE VALUES")
    print("Quantity equal zero:", (harvested["quantity_reported"] == 0).sum())
    print("Quantity below zero:", (harvested["quantity_reported"] < 0).sum())
    print("Value equal zero:", (harvested["estimated_value_reported"] == 0).sum())
    print("Value below zero:", (harvested["estimated_value_reported"] < 0).sum())

    keep = [
        "source_module", "household_id", "plot_number", "crop_code",
        "harvested", "area_harvested_acres",
        "quantity_reported", "estimated_value_reported",
        "value_per_reported_quantity_unit"
    ]

    output = maize[[
        "source_module", "household_id", "plot_number", "crop_code",
        "harvested", "area_harvested_acres",
        "quantity_reported", "estimated_value_reported"
    ]].copy()

    output["value_per_reported_quantity_unit"] = (
        output["estimated_value_reported"] / output["quantity_reported"]
    )

    results.append(output)

if results:

    combined = pd.concat(results, ignore_index=True)

    if AUDIT_FILE.exists():

        audit = pd.read_csv(AUDIT_FILE)

        keys = ["source_module", "household_id", "plot_number", "crop_code"]

        audit_keys = audit[keys].copy()
        audit_keys["household_id"] = audit_keys["household_id"].astype(str)

        combined = combined.merge(
            audit_keys,
            on=keys,
            how="left",
            validate="one_to_one",
            indicator=True
        )

        print("\nAUDIT MATCHING")
        print(combined["_merge"].value_counts(dropna=False))

        combined.drop(columns=["_merge"], inplace=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT_FILE, index=False)

    print("\nREVIEW FILE CREATED:", OUTPUT_FILE)
    print("Total maize records exported:", len(combined))

print("\nQUANTITY-VALUE INVESTIGATION COMPLETE.")
print("RAW NPS DATA WAS NOT MODIFIED.")
print("IMPORTANT: Value/quantity ratio is NOT proof of KG conversion.")
