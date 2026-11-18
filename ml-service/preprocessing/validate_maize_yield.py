from pathlib import Path
import numpy as np
import pandas as pd
import pyreadstat

# ============================================================
# AFIP - MAIZE YIELD VALIDATION
# ============================================================

AUDIT_FILE = Path("data/processed/maize_yield_audit.csv")

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

OUTPUT_DIR = Path("data/processed")

OUTPUT_ALL = OUTPUT_DIR / "maize_yield_validation.csv"
OUTPUT_ISSUES = OUTPUT_DIR / "maize_yield_validation_issues.csv"
OUTPUT_SUMMARY = OUTPUT_DIR / "maize_yield_validation_summary.txt"

ACRE_TO_HECTARE = 2.47105

MODULES = {
    "AG_SEC_4A": {
        "file": "AG_SEC_4A.dta",
        "harvested": "ag4a_19",
        "area": "ag4a_21",
        "quantity": "ag4a_27",
    },
    "AG_SEC_4B": {
        "file": "AG_SEC_4B.dta",
        "harvested": "ag4b_19",
        "area": "ag4b_21",
        "quantity": "ag4b_28",
    },
}

KEYS = [
    "source_module",
    "household_id",
    "plot_number",
    "crop_code",
]


def add_issue(existing, issue):
    if existing:
        return existing + ";" + issue
    return issue


def main():

    print("=" * 80)
    print("AFIP - MAIZE YIELD VALIDATION")
    print("=" * 80)

    if not AUDIT_FILE.exists():
        raise FileNotFoundError(
            f"Yield audit file not found: {AUDIT_FILE}"
        )

    audit = pd.read_csv(AUDIT_FILE)

    required_audit = KEYS + [
        "area_harvested_acres",
        "quantity_reported",
        "yield_kg_per_acre",
        "yield_kg_per_hectare",
    ]

    missing = [
        column for column in required_audit
        if column not in audit.columns
    ]

    if missing:
        raise ValueError(
            f"Missing audit columns: {missing}"
        )

    audit["household_id"] = (
        audit["household_id"].astype(str)
    )

    audit["source_module"] = (
        audit["source_module"].astype(str)
    )

    if audit.duplicated(KEYS).any():
        raise ValueError(
            "Duplicate observations found in audit keys. "
            "Resolve duplicates before validation."
        )

    print("Audit records:", len(audit))

    raw_frames = []

    # --------------------------------------------------------
    # 1. READ RAW DATA AND EXTRACT MAIZE OBSERVATIONS
    # --------------------------------------------------------

    for module, config in MODULES.items():

        path = ROOT / config["file"]

        if not path.exists():
            raise FileNotFoundError(path)

        raw, meta = pyreadstat.read_dta(str(path))

        maize = raw[
            raw["cropid"] == 11
        ].copy()

        harvested = maize[
            maize[config["harvested"]] == 1
        ].copy()

        extracted = pd.DataFrame({
            "source_module": module,
            "household_id": harvested["sdd_hhid"].astype(str),
            "plot_number": harvested["plotnum"],
            "crop_code": harvested["cropid"],
            "raw_harvested": harvested[config["harvested"]],
            "raw_area_acres": harvested[config["area"]],
            "raw_quantity": harvested[config["quantity"]],
        })

        raw_frames.append(extracted)

        print(
            f"{module}: maize={len(maize)}, "
            f"harvested={len(harvested)}"
        )

    raw_all = pd.concat(
        raw_frames,
        ignore_index=True
    )

    if raw_all.duplicated(KEYS).any():
        raise ValueError(
            "Duplicate raw observations found for matching keys."
        )

    # --------------------------------------------------------
    # 2. MATCH AUDIT AGAINST RAW DATA
    # --------------------------------------------------------

    validated = audit.merge(
        raw_all,
        on=KEYS,
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    matched = validated[
        validated["_merge"] == "both"
    ].copy()

    unmatched = validated[
        validated["_merge"] != "both"
    ].copy()

    print("\nRAW MATCHING")
    print("Matched:", len(matched))
    print("Unmatched:", len(unmatched))

    if len(unmatched) > 0:
        unmatched["validation_issues"] = (
            "RAW_RECORD_NOT_MATCHED"
        )

    # --------------------------------------------------------
    # 3. NUMERIC CONVERSION FOR VALIDATION
    # --------------------------------------------------------

    numeric_columns = [
        "area_harvested_acres",
        "quantity_reported",
        "yield_kg_per_acre",
        "yield_kg_per_hectare",
        "raw_area_acres",
        "raw_quantity",
    ]

    for column in numeric_columns:
        matched[column] = pd.to_numeric(
            matched[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # 4. VALIDATION RULES
    # --------------------------------------------------------

    matched["validation_issues"] = ""

    def flag(mask, issue):
        for index in matched.index[mask.fillna(False)]:
            matched.at[index, "validation_issues"] = add_issue(
                matched.at[index, "validation_issues"],
                issue,
            )

    flag(
        matched["raw_harvested"] != 1,
        "RAW_NOT_MARKED_HARVESTED",
    )

    flag(
        matched["area_harvested_acres"].isna(),
        "AREA_MISSING",
    )

    flag(
        matched["quantity_reported"].isna(),
        "QUANTITY_MISSING",
    )

    flag(
        matched["raw_area_acres"].isna(),
        "RAW_AREA_MISSING",
    )

    flag(
        matched["raw_quantity"].isna(),
        "RAW_QUANTITY_MISSING",
    )

    flag(
        matched["area_harvested_acres"] <= 0,
        "AREA_NOT_POSITIVE",
    )

    flag(
        matched["quantity_reported"] < 0,
        "NEGATIVE_QUANTITY",
    )

    flag(
        matched["quantity_reported"] == 0,
        "ZERO_QUANTITY",
    )

    # Compare processed values against original Stata values.
    area_equal = np.isclose(
        matched["area_harvested_acres"],
        matched["raw_area_acres"],
        rtol=0,
        atol=1e-9,
        equal_nan=True,
    )

    quantity_equal = np.isclose(
        matched["quantity_reported"],
        matched["raw_quantity"],
        rtol=0,
        atol=1e-9,
        equal_nan=True,
    )

    flag(
        pd.Series(~area_equal, index=matched.index),
        "AREA_RAW_MISMATCH",
    )

    flag(
        pd.Series(~quantity_equal, index=matched.index),
        "QUANTITY_RAW_MISMATCH",
    )

    # --------------------------------------------------------
    # 5. RECOMPUTE YIELD
    # --------------------------------------------------------

    valid_area = (
        matched["area_harvested_acres"].notna()
        & (matched["area_harvested_acres"] > 0)
    )

    valid_quantity = (
        matched["quantity_reported"].notna()
        & (matched["quantity_reported"] >= 0)
    )

    calculable = valid_area & valid_quantity

    matched["recomputed_kg_per_acre"] = np.nan
    matched["recomputed_kg_per_hectare"] = np.nan

    matched.loc[
        calculable,
        "recomputed_kg_per_acre"
    ] = (
        matched.loc[calculable, "quantity_reported"]
        / matched.loc[calculable, "area_harvested_acres"]
    )

    matched.loc[
        calculable,
        "recomputed_kg_per_hectare"
    ] = (
        matched.loc[calculable, "recomputed_kg_per_acre"]
        * ACRE_TO_HECTARE
    )

    acre_equal = np.isclose(
        matched["yield_kg_per_acre"],
        matched["recomputed_kg_per_acre"],
        rtol=1e-7,
        atol=1e-8,
        equal_nan=True,
    )

    hectare_equal = np.isclose(
        matched["yield_kg_per_hectare"],
        matched["recomputed_kg_per_hectare"],
        rtol=1e-7,
        atol=1e-8,
        equal_nan=True,
    )

    flag(
        pd.Series(~acre_equal, index=matched.index),
        "YIELD_KG_PER_ACRE_MISMATCH",
    )

    flag(
        pd.Series(~hectare_equal, index=matched.index),
        "YIELD_KG_PER_HECTARE_MISMATCH",
    )

    # --------------------------------------------------------
    # 6. REVIEW FLAGS
    # --------------------------------------------------------

    matched["yield_review"] = "REQUIRES_UNIT_VERIFICATION"

    matched.loc[
        matched["recomputed_kg_per_hectare"].notna(),
        "yield_review"
    ] = "CALCULATION_CHECKED_UNIT_UNVERIFIED"

    matched.loc[
        matched["validation_issues"] != "",
        "yield_review"
    ] = "DATA_QUALITY_REVIEW"

    # These are investigation bands only, not agronomic rules.
    matched["provisional_screening_flag"] = "NOT_SCREENED"

    matched.loc[
        matched["recomputed_kg_per_hectare"] < 100,
        "provisional_screening_flag"
    ] = "BELOW_100_REVIEW"

    matched.loc[
        matched["recomputed_kg_per_hectare"] > 20000,
        "provisional_screening_flag"
    ] = "ABOVE_20000_REVIEW"

    # --------------------------------------------------------
    # 7. COMBINE RESULTS
    # --------------------------------------------------------

    unmatched["yield_review"] = "RAW_RECORD_NOT_MATCHED"
    unmatched["provisional_screening_flag"] = "NOT_SCREENED"

    all_results = pd.concat(
        [matched, unmatched],
        ignore_index=True,
        sort=False,
    )

    issues = all_results[
        all_results["validation_issues"].fillna("") != ""
    ].copy()

    # --------------------------------------------------------
    # 8. EXPORT REPORTS
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    all_results.to_csv(
        OUTPUT_ALL,
        index=False
    )

    issues.to_csv(
        OUTPUT_ISSUES,
        index=False
    )

    # --------------------------------------------------------
    # 9. SUMMARY
    # --------------------------------------------------------

    lines = []

    lines.append("AFIP MAIZE YIELD VALIDATION SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Audit observations: {len(audit)}")
    lines.append(f"Raw harvested maize observations: {len(raw_all)}")
    lines.append(f"Matched observations: {len(matched)}")
    lines.append(f"Unmatched observations: {len(unmatched)}")
    lines.append(f"Observations with data quality issues: {len(issues)}")

    lines.append("")
    lines.append("YIELD CALCULATION STATISTICS")
    lines.append(
        matched["recomputed_kg_per_hectare"].describe().to_string()
    )

    lines.append("")
    lines.append("PROVISIONAL SCREENING FLAGS")
    lines.append(
        matched["provisional_screening_flag"]
        .value_counts(dropna=False)
        .to_string()
    )

    lines.append("")
    lines.append("VALIDATION ISSUES")
    lines.append(
        issues["validation_issues"]
        .value_counts(dropna=False)
        .to_string()
    )

    lines.append("")
    lines.append("IMPORTANT LIMITATIONS")
    lines.append(
        "1. Questionnaire specifies conversion of local units to KG."
    )
    lines.append(
        "2. Record-level quantity conversion is not independently verified."
    )
    lines.append(
        "3. Yield calculations are conditional on quantity being KG."
    )
    lines.append(
        "4. Screening thresholds are investigation flags, not agronomic verdicts."
    )
    lines.append(
        "5. No model training was performed."
    )
    lines.append(
        "6. Raw NPS data was not modified."
    )

    summary = "\n".join(lines)

    OUTPUT_SUMMARY.write_text(
        summary,
        encoding="utf-8"
    )

    print("\n" + summary)

    print("\nOUTPUT FILES")
    print(OUTPUT_ALL)
    print(OUTPUT_ISSUES)
    print(OUTPUT_SUMMARY)

    print("\nYIELD VALIDATION SCRIPT COMPLETED.")
    print("RAW NPS DATA WAS NOT MODIFIED.")
    print("MODEL TRAINING WAS NOT STARTED.")


if __name__ == "__main__":
    main()
