from pathlib import Path
import pandas as pd
import numpy as np
import pyreadstat

BASE = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

FILES = {
    "AG_SEC_4A.dta": "ag4a",
    "AG_SEC_4B.dta": "ag4b",
}

def audit(df, prefix, scope):
    print("\n" + "=" * 100)
    print("SCOPE:", scope)
    print("=" * 100)

    q_total = f"{prefix}_10_1"
    u_total = f"{prefix}_10_2"

    q_prev = f"{prefix}_10a_1"
    u_prev = f"{prefix}_10a_2"

    q_buy = f"{prefix}_10c_1"
    u_buy = f"{prefix}_10c_2"

    columns = [
        "sdd_hhid", "plotnum", "cropid",
        q_total, u_total,
        q_prev, u_prev,
        q_buy, u_buy,
    ]

    data = df[columns].copy()

    # Quantities must be numeric.
    quantities = [q_total, q_prev, q_buy]

    for col in quantities:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    print("\n1. SOURCE QUANTITY COMPLETENESS")

    for name, q, u in [
        ("TOTAL", q_total, u_total),
        ("PREVIOUS", q_prev, u_prev),
        ("PURCHASED", q_buy, u_buy),
    ]:
        print(
            name,
            "| positive:", (data[q] > 0).sum(),
            "| zero:", (data[q] == 0).sum(),
            "| missing:", data[q].isna().sum(),
        )

    print("\n2. UNIT COMPATIBILITY")

    positive = (
        (data[q_total] > 0)
        & (data[q_prev] > 0)
        & (data[q_buy] > 0)
    )

    print("All three quantities positive:", positive.sum())

    print("\nTOTAL vs PREVIOUS UNIT:")
    print(pd.crosstab(data[u_total], data[u_prev]))

    print("\nTOTAL vs PURCHASED UNIT:")
    print(pd.crosstab(data[u_total], data[u_buy]))

    # Only compare quantities if all positive components
    # use the same known unit (codes 1-4).
    total_known = data[u_total].isin([1, 2, 3, 4])

    prev_compatible = (
        (data[q_prev] == 0)
        | (
            (data[q_prev] > 0)
            & (data[u_prev] == data[u_total])
        )
    )

    buy_compatible = (
        (data[q_buy] == 0)
        | (
            (data[q_buy] > 0)
            & (data[u_buy] == data[u_total])
        )
    )

    complete = (
        data[q_total].notna()
        & data[q_prev].notna()
        & data[q_buy].notna()
    )

    eligible = (
        complete
        & total_known
        & prev_compatible
        & buy_compatible
    )

    print("\n3. COMPARISON ELIGIBILITY")
    print("Complete quantities:", complete.sum())
    print("Same known unit (codes 1-4):", eligible.sum())
    print("Not eligible:", (~eligible).sum())

    # Arithmetic only on compatible observations.
    result = data.loc[eligible].copy()

    result["source_sum"] = (
        result[q_prev] + result[q_buy]
    )

    result["difference"] = (
        result[q_total] - result["source_sum"]
    )

    tolerance = 1e-9

    result["status"] = np.select(
        [
            result["difference"] < -tolerance,
            result["difference"].abs() <= tolerance,
        ],
        [
            "SOURCE_SUM_EXCEEDS_TOTAL",
            "SOURCES_EQUAL_TOTAL",
        ],
        default="TOTAL_EXCEEDS_REPORTED_SOURCES",
    )

    print("\n4. CONSISTENCY RESULTS")

    print(result["status"].value_counts())

    print("\n5. DETAILED FLAGGED RECORDS")

    flagged = result[
        result["status"] == "SOURCE_SUM_EXCEEDS_TOTAL"
    ]

    print("Flagged records:", len(flagged))

    display = [
        "sdd_hhid", "plotnum", "cropid",
        q_total, u_total,
        q_prev, u_prev,
        q_buy, u_buy,
        "source_sum", "difference",
    ]

    print(
        flagged[display]
        .to_string(index=False)
    )

    print("\n6. TOTAL EXCEEDS REPORTED SOURCES")

    remainder = result[
        result["status"] == "TOTAL_EXCEEDS_REPORTED_SOURCES"
    ]

    print("Records:", len(remainder))

    print(
        remainder[display]
        .head(20)
        .to_string(index=False)
    )

    print("\n7. MAIZE-ONLY RESULTS")

    maize = result[result["cropid"] == 11]

    print("Eligible maize records:", len(maize))
    print(maize["status"].value_counts())

    print("\n8. MAIZE FLAGGED RECORDS")

    maize_flagged = maize[
        maize["status"] == "SOURCE_SUM_EXCEEDS_TOTAL"
    ]

    print(
        maize_flagged[display]
        .to_string(index=False)
    )


for filename, prefix in FILES.items():
    print("\n" + "#" * 100)
    print("FILE:", filename)
    print("#" * 100)

    df, meta = pyreadstat.read_dta(str(BASE / filename))

    audit(df, prefix, "ALL CROPS")

print("\nSEED SOURCE CONSISTENCY AUDIT COMPLETED.")
print("RAW DATA WAS NOT MODIFIED.")
print("NO UNIT CONVERSION WAS PERFORMED.")
print("NO CLEANING WAS PERFORMED.")
print("MODEL TRAINING WAS NOT STARTED.")
