from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

# ============================================================
# AFIP - SEED QUANTITY TRAINING/TESTING SPLIT AUDIT
# READ ONLY - NO CLEANING - NO TRAINING
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from train_all_models import prepare_seed_quantity_data


def main():

    print("=" * 90)
    print("AFIP SEED QUANTITY RECORD SPLIT AUDIT")
    print("READ ONLY - NO MODEL TRAINING")
    print("=" * 90)

    # Reuse the exact data preparation function.
    X, y, groups, numeric_features, categorical_features, audit = (
        prepare_seed_quantity_data()
    )

    print("\n1. DATASET SUMMARY")
    print("-" * 90)

    print("Original rows:", audit["original_rows"])
    print("Eligible rows:", len(X))
    print("Unique households:", groups.nunique())
    print("Target:", audit["target"])
    print("Target unit:", audit["target_unit"])
    print("Features:", list(X.columns))

    if len(X) < 50:
        raise ValueError("Insufficient eligible records.")

    if groups.nunique() < 5:
        raise ValueError("Insufficient unique households.")

    # Reproduce the exact training split.
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=42
    )

    train_indices, test_indices = next(
        splitter.split(X, y, groups=groups)
    )

    train_set = set(train_indices.tolist())
    test_set = set(test_indices.tolist())

    print("\n2. SPLIT SUMMARY")
    print("-" * 90)

    print("Training records:", len(train_indices))
    print("Testing records:", len(test_indices))

    print(
        "Training percentage:",
        round(len(train_indices) / len(X) * 100, 2),
        "%"
    )

    print(
        "Testing percentage:",
        round(len(test_indices) / len(X) * 100, 2),
        "%"
    )

    # Verify that households do not overlap.
    train_households = set(
        groups.iloc[train_indices].tolist()
    )

    test_households = set(
        groups.iloc[test_indices].tolist()
    )

    overlap = train_households.intersection(test_households)

    print("Training households:", len(train_households))
    print("Testing households:", len(test_households))
    print("Overlapping households:", len(overlap))

    if overlap:
        raise AssertionError(
            "DATA LEAKAGE WARNING: Household overlap detected."
        )

    # Find every eligible record with target = 10 KG.
    target_values = y.to_numpy(dtype=float)

    ten_kg_positions = np.flatnonzero(
        np.isclose(
            target_values,
            10.0,
            rtol=0,
            atol=1e-9
        )
    )

    print("\n3. ACTUAL SEED QUANTITY = 10 KG")
    print("-" * 90)

    print("Number of eligible 10 KG records:", len(ten_kg_positions))

    results = []

    for position in ten_kg_positions:

        original_index = X.index[position]

        if position in train_set:
            membership = "TRAINING"
        elif position in test_set:
            membership = "TESTING"
        else:
            membership = "UNKNOWN"

        row = {
            "original_row_index": original_index,
            "household_id": groups.iloc[position],
            "actual_seed_quantity_kg": y.iloc[position],
            "dataset_position": position,
            "split_membership": membership
        }

        for feature in X.columns:
            row[feature] = X.iloc[position][feature]

        results.append(row)

    if results:

        result_df = pd.DataFrame(results)

        print(
            result_df.to_string(
                index=False,
                max_rows=100
            )
        )

        print("\n4. MEMBERSHIP SUMMARY")
        print("-" * 90)

        print(
            result_df["split_membership"].value_counts(
                dropna=False
            ).to_string()
        )

    else:
        print("No eligible record with actual quantity of 10 KG found.")

    print("\n5. AUDIT VALIDATION")
    print("-" * 90)

    print("Training and testing positions overlap:",
          bool(train_set.intersection(test_set)))

    print("All records assigned:",
          len(train_set.union(test_set)) == len(X))

    print("Household overlap:", len(overlap))

    print("\n" + "=" * 90)
    print("AUDIT COMPLETED")
    print("RAW NPS DATA WAS NOT MODIFIED.")
    print("EXISTING MODEL WAS NOT MODIFIED.")
    print("NO MODEL WAS TRAINED.")
    print("=" * 90)


if __name__ == "__main__":
    main()

