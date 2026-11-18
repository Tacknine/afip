from pathlib import Path
import pandas as pd
import pyreadstat

BASE = Path("data/processed")
AUDIT = BASE / "maize_yield_validation.csv"
OUTPUT = BASE / "maize_agronomic_review.csv"
LOW_OUTPUT = BASE / "maize_agronomic_low_yield.csv"
HIGH_OUTPUT = BASE / "maize_agronomic_high_yield.csv"
REPORT = BASE / "maize_agronomic_review_summary.txt"

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

REFERENCE_YIELD = 1500.0

MODULES = {
    "AG_SEC_4A": {
        "file": "AG_SEC_4A.dta",
        "loss": "ag4a_17",
        "area_less": "ag4a_22",
        "begin": "ag4a_24_1",
        "end": "ag4a_24_2",
    },
    "AG_SEC_4B": {
        "file": "AG_SEC_4B.dta",
        "loss": "ag4b_17",
        "area_less": "ag4b_22",
        "begin": "ag4b_24_1",
        "end": "ag4b_24_2",
    },
}

KEYS = [
    "source_module",
    "household_id",
    "plot_number",
    "crop_code",
]


def main():

    print("=" * 85)
    print("AFIP - MAIZE AGRONOMIC YIELD REVIEW")
    print("=" * 85)

    if not AUDIT.exists():
        raise FileNotFoundError(AUDIT)

    audit = pd.read_csv(AUDIT)

    audit = audit[
        audit["yield_kg_per_hectare"].notna()
    ].copy()

    audit["household_id"] = audit["household_id"].astype(str)

    raw_frames = []

    # --------------------------------------------------
    # 1. EXTRACT AGRONOMIC VARIABLES FROM RAW NPS
    # --------------------------------------------------

    for module, config in MODULES.items():

        df, meta = pyreadstat.read_dta(
            str(ROOT / config["file"])
        )

        maize = df[
            (df["cropid"] == 11)
            & (df[config["file"].replace(".dta", "")[:0] + (
                "ag4a_19" if module == "AG_SEC_4A" else "ag4b_19"
            )] == 1)
        ].copy()

        extracted = pd.DataFrame({
            "source_module": module,
            "household_id": maize["sdd_hhid"].astype(str),
            "plot_number": maize["plotnum"],
            "crop_code": maize["cropid"],
            "loss_before_harvest": maize[config["loss"]],
            "area_harvested_less_than_planted": maize[config["area_less"]],
            "harvest_begin_month": maize[config["begin"]],
            "harvest_end_month": maize[config["end"]],
        })

        if module == "AG_SEC_4B":
            extracted["harvest_completed"] = maize["ag4b_25"]

        raw_frames.append(extracted)

    raw = pd.concat(raw_frames, ignore_index=True)

    if raw.duplicated(KEYS).any():
        raise ValueError("Duplicate raw keys detected.")

    # --------------------------------------------------
    # 2. MATCH VALIDATED YIELD WITH RAW VARIABLES
    # --------------------------------------------------

    if "_merge" in audit.columns:
        audit = audit.drop(columns=["_merge"])

    review = audit.merge(
        raw,
        on=KEYS,
        how="left",
        validate="one_to_one",
        indicator="raw_match_status",
    )

    print("\nRAW MATCHING")
    print(review["raw_match_status"].value_counts())

    review["raw_context_match"] = (
        review["raw_match_status"] == "both"
    )

    review.drop(columns=["raw_match_status"], inplace=True)

    review["yield_kg_per_hectare"] = pd.to_numeric(
        review["yield_kg_per_hectare"],
        errors="coerce",
    )

    # --------------------------------------------------
    # 3. DESCRIPTIVE YIELD BANDS
    # These are NOT agronomic pass/fail thresholds.
    # --------------------------------------------------

    bins = [
        float("-inf"),
        500,
        1000,
        2000,
        3000,
        float("inf"),
    ]

    labels = [
        "BELOW_500",
        "500_TO_999",
        "1000_TO_1999",
        "2000_TO_2999",
        "3000_AND_ABOVE",
    ]

    review["descriptive_yield_band"] = pd.cut(
        review["yield_kg_per_hectare"],
        bins=bins,
        labels=labels,
        right=False,
    )

    review["comparison_to_nbs_1500"] = (
        review["yield_kg_per_hectare"]
        .apply(
            lambda x:
                "BELOW_REFERENCE"
                if x < REFERENCE_YIELD
                else "AT_OR_ABOVE_REFERENCE"
        )
    )

    # --------------------------------------------------
    # 4. LOW AND HIGH OBSERVATIONS
    # --------------------------------------------------

    low = review.nsmallest(
        30,
        "yield_kg_per_hectare"
    ).copy()

    high = review.nlargest(
        30,
        "yield_kg_per_hectare"
    ).copy()

    # --------------------------------------------------
    # 5. SUMMARY BY SEASON
    # --------------------------------------------------

    print("\nYIELD SUMMARY BY SEASON")

    season_summary = review.groupby(
        "season",
        observed=True
    )["yield_kg_per_hectare"].agg(
        ["count", "mean", "median", "min", "max", "std"]
    )

    print(season_summary.to_string())

    print("\nDESCRIPTIVE YIELD BANDS")
    print(
        review["descriptive_yield_band"]
        .value_counts(sort=False)
        .to_string()
    )

    print("\nCOMPARISON WITH NBS REFERENCE OF 1500 KG/HA")
    print(
        review["comparison_to_nbs_1500"]
        .value_counts()
        .to_string()
    )

    # --------------------------------------------------
    # 6. CROP LOSS ASSOCIATION
    # --------------------------------------------------

    print("\nYIELD BY CROP LOSS STATUS")
    print(
        review.groupby(
            ["source_module", "loss_before_harvest"],
            dropna=False
        )["yield_kg_per_hectare"]
        .agg(["count", "mean", "median"])
        .to_string()
    )

    print("\nYIELD BY AREA HARVESTED LESS THAN PLANTED")
    print(
        review.groupby(
            ["source_module", "area_harvested_less_than_planted"],
            dropna=False
        )["yield_kg_per_hectare"]
        .agg(["count", "mean", "median"])
        .to_string()
    )

    # --------------------------------------------------
    # 7. HARVEST MONTHS
    # --------------------------------------------------

    print("\nHARVEST BEGIN MONTH DISTRIBUTION")
    print(
        review.groupby(
            ["source_module", "harvest_begin_month"],
            dropna=False
        ).size().to_string()
    )

    print("\nHARVEST END MONTH DISTRIBUTION")
    print(
        review.groupby(
            ["source_module", "harvest_end_month"],
            dropna=False
        ).size().to_string()
    )

    # --------------------------------------------------
    # 8. LOWEST AND HIGHEST OBSERVATIONS
    # --------------------------------------------------

    columns = [
        "source_module",
        "household_id",
        "plot_number",
        "season",
        "area_harvested_acres",
        "quantity_reported",
        "yield_kg_per_hectare",
        "loss_before_harvest",
        "area_harvested_less_than_planted",
        "harvest_begin_month",
        "harvest_end_month",
    ]

    columns = [
        c for c in columns if c in review.columns
    ]

    print("\n30 LOWEST YIELD OBSERVATIONS")
    print(low[columns].to_string(index=False))

    print("\n30 HIGHEST YIELD OBSERVATIONS")
    print(high[columns].to_string(index=False))

    # --------------------------------------------------
    # 9. EXPORT RESULTS
    # --------------------------------------------------

    BASE.mkdir(parents=True, exist_ok=True)

    review.to_csv(OUTPUT, index=False)
    low.to_csv(LOW_OUTPUT, index=False)
    high.to_csv(HIGH_OUTPUT, index=False)

    lines = [
        "AFIP MAIZE AGRONOMIC REVIEW",
        "=" * 70,
        f"Observations reviewed: {len(review)}",
        f"Matched raw context: {review['raw_context_match'].sum()}",
        "",
        "YIELD SUMMARY BY SEASON",
        season_summary.to_string(),
        "",
        "DESCRIPTIVE YIELD BANDS",
        review["descriptive_yield_band"].value_counts(
            sort=False
        ).to_string(),
        "",
        "COMPARISON WITH NBS REFERENCE",
        review["comparison_to_nbs_1500"].value_counts().to_string(),
        "",
        "LIMITATIONS",
        "Quantity unit conversion has not been independently verified.",
        "Yield values remain conditional on quantity being KG.",
        "Descriptive bands are not agronomic pass/fail rules.",
        "National average is contextual, not a farm-level threshold.",
        "Raw NPS data was not modified.",
        "No model training was performed.",
    ]

    REPORT.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print("\nOUTPUT FILES")
    print(OUTPUT)
    print(LOW_OUTPUT)
    print(HIGH_OUTPUT)
    print(REPORT)

    print("\nAGRONOMIC REVIEW COMPLETED.")
    print("RAW NPS DATA WAS NOT MODIFIED.")
    print("MODEL TRAINING WAS NOT STARTED.")


if __name__ == "__main__":
    main()
