import json
import logging
import shutil
from pathlib import Path
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.model_selection import GroupShuffleSplit, GroupKFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from train_all_models import prepare_seed_quantity_data


# ============================================================
# AFIP - PRODUCTION SEED QUANTITY TRAINING
# Target: Actual seed quantity in KG
# Household grouped validation
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ARTIFACT_DIR = BASE_DIR / "artifacts" / "seed_quantity"
BACKUP_DIR = BASE_DIR / "artifacts" / "backups" / "seed_quantity"

REPORT_DIR = BASE_DIR / "audit_results"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("AFIP.SEED.PRODUCTION")


def create_preprocessor(numeric_features, categorical_features):

    transformers = []

    if numeric_features:
        transformers.append((
            "numeric",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median"))
            ]),
            numeric_features
        ))

    if categorical_features:
        transformers.append((
            "categorical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                (
                    "encoder",
                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=False
                    )
                )
            ]),
            categorical_features
        ))

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop"
    )


def create_candidates(numeric_features, categorical_features):

    return {
        "random_forest": Pipeline([
            (
                "preprocessor",
                create_preprocessor(
                    numeric_features,
                    categorical_features
                )
            ),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=500,
                    max_depth=12,
                    min_samples_split=8,
                    min_samples_leaf=4,
                    max_features=0.8,
                    random_state=42,
                    n_jobs=-1
                )
            )
        ]),

        "extra_trees": Pipeline([
            (
                "preprocessor",
                create_preprocessor(
                    numeric_features,
                    categorical_features
                )
            ),
            (
                "regressor",
                ExtraTreesRegressor(
                    n_estimators=500,
                    max_depth=12,
                    min_samples_split=8,
                    min_samples_leaf=4,
                    max_features=0.8,
                    random_state=42,
                    n_jobs=-1
                )
            )
        ])
    }


def calculate_metrics(actual, predicted):

    predicted = np.maximum(
        np.asarray(predicted, dtype=float),
        0.0
    )

    actual = np.asarray(actual, dtype=float)

    return {
        "mae_kg": float(
            mean_absolute_error(actual, predicted)
        ),
        "rmse_kg": float(
            np.sqrt(mean_squared_error(actual, predicted))
        ),
        "r2": float(
            r2_score(actual, predicted)
        ),
        "mean_actual_kg": float(np.mean(actual)),
        "mean_predicted_kg": float(np.mean(predicted)),
        "prediction_bias_kg": float(
            np.mean(predicted - actual)
        )
    }


def main():

    logger.info("=" * 75)
    logger.info("AFIP SEED QUANTITY PRODUCTION TRAINING")
    logger.info("=" * 75)

    (
        X,
        y,
        groups,
        numeric_features,
        categorical_features,
        audit
    ) = prepare_seed_quantity_data()

    if len(X) < 50:
        raise ValueError("Insufficient eligible training records.")

    if groups.nunique() < 10:
        raise ValueError("Insufficient unique households.")

    if not np.isfinite(y.to_numpy(dtype=float)).all():
        raise ValueError("Target contains non-finite values.")

    if (y <= 0).any():
        raise ValueError("Target contains invalid quantities.")

    feature_columns = list(X.columns)

    logger.info("Eligible records: %s", len(X))
    logger.info("Unique households: %s", groups.nunique())
    logger.info("Features: %s", feature_columns)
    logger.info("Target: actual KG, without log transformation")

    # --------------------------------------------------------
    # 1. HOUSEHOLD HOLDOUT
    # --------------------------------------------------------

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=42
    )

    train_idx, test_idx = next(
        splitter.split(X, y, groups=groups)
    )

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    train_groups = groups.iloc[train_idx]
    test_groups = groups.iloc[test_idx]

    if set(train_groups).intersection(set(test_groups)):
        raise AssertionError("Household leakage detected.")

    if len(test_idx) < 20:
        raise ValueError("Insufficient held-out test records.")

    logger.info("Training rows: %s", len(X_train))
    logger.info("Testing rows: %s", len(X_test))

    # --------------------------------------------------------
    # 2. GROUP CROSS VALIDATION
    # --------------------------------------------------------

    candidates = create_candidates(
        numeric_features,
        categorical_features
    )

    n_splits = min(5, train_groups.nunique())

    cv = GroupKFold(n_splits=n_splits)

    cv_results = {}

    for name, estimator in candidates.items():

        logger.info("Cross-validating %s", name)

        fold_mae = []
        fold_rmse = []

        for fold, (fit_idx, val_idx) in enumerate(
            cv.split(X_train, y_train, groups=train_groups),
            start=1
        ):

            fold_model = create_candidates(
                numeric_features,
                categorical_features
            )[name]

            fold_model.fit(
                X_train.iloc[fit_idx],
                y_train.iloc[fit_idx]
            )

            predictions = np.maximum(
                fold_model.predict(X_train.iloc[val_idx]),
                0.0
            )

            fold_metrics = calculate_metrics(
                y_train.iloc[val_idx],
                predictions
            )

            fold_mae.append(fold_metrics["mae_kg"])
            fold_rmse.append(fold_metrics["rmse_kg"])

            logger.info(
                "%s fold %s MAE: %.4f KG",
                name,
                fold,
                fold_metrics["mae_kg"]
            )

        cv_results[name] = {
            "mean_mae_kg": float(np.mean(fold_mae)),
            "std_mae_kg": float(np.std(fold_mae)),
            "mean_rmse_kg": float(np.mean(fold_rmse)),
            "folds": len(fold_mae)
        }

    # --------------------------------------------------------
    # 3. SELECT BEST ALGORITHM
    # --------------------------------------------------------

    best_name = min(
        cv_results,
        key=lambda name: cv_results[name]["mean_mae_kg"]
    )

    logger.info("Selected algorithm: %s", best_name)

    selected_model = candidates[best_name]

    # Train only on training partition before final evaluation.
    selected_model.fit(X_train, y_train)

    test_predictions = np.maximum(
        selected_model.predict(X_test),
        0.0
    )

    test_metrics = calculate_metrics(
        y_test,
        test_predictions
    )

    # Baseline: training median.
    baseline_predictions = np.full(
        len(y_test),
        float(y_train.median())
    )

    baseline_mae = mean_absolute_error(
        y_test,
        baseline_predictions
    )

    improvement = (
        (baseline_mae - test_metrics["mae_kg"])
        / baseline_mae
        * 100
        if baseline_mae > 0 else 0.0
    )

    validation_passed = (
        np.isfinite(test_metrics["mae_kg"])
        and np.isfinite(test_metrics["rmse_kg"])
        and np.isfinite(test_metrics["r2"])
        and test_metrics["mae_kg"] < baseline_mae
        and cv_results[best_name]["mean_mae_kg"] < float("inf")
    )

    logger.info("=" * 75)
    logger.info("HELD-OUT EVALUATION")
    logger.info("Algorithm: %s", best_name)
    logger.info("MAE: %.4f KG", test_metrics["mae_kg"])
    logger.info("RMSE: %.4f KG", test_metrics["rmse_kg"])
    logger.info("R2: %.4f", test_metrics["r2"])
    logger.info("Baseline MAE: %.4f KG", baseline_mae)
    logger.info("Baseline improvement: %.2f%%", improvement)
    logger.info("Validation passed: %s", validation_passed)

    # --------------------------------------------------------
    # 4. AUDIT 10 KG RECORDS
    # --------------------------------------------------------

    ten_mask = np.isclose(
        y_test.to_numpy(dtype=float),
        10.0,
        rtol=0,
        atol=1e-9
    )

    ten_records = []

    for position in np.flatnonzero(ten_mask):

        ten_records.append({
            "household_id": str(test_groups.iloc[position]),
            "actual_kg": float(y_test.iloc[position]),
            "predicted_kg": float(test_predictions[position]),
            "absolute_error_kg": float(
                abs(y_test.iloc[position] - test_predictions[position])
            )
        })

    # --------------------------------------------------------
    # 5. SAVE EVALUATION REPORT
    # --------------------------------------------------------

    report = {
        "model_name": "seed_quantity",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "selected_algorithm": best_name,
        "target": "ag4a_10_1",
        "target_unit": "KG",
        "target_transformation": "none",
        "feature_columns": feature_columns,
        "cross_validation": cv_results,
        "test_metrics": test_metrics,
        "baseline_mae_kg": float(baseline_mae),
        "baseline_improvement_percent": float(improvement),
        "validation_status": (
            "passed" if validation_passed else "failed"
        ),
        "test_records": len(X_test),
        "training_records": len(X_train),
        "ten_kg_test_records": ten_records,
        "data_audit": audit
    }

    report_path = (
        REPORT_DIR / "seed_quantity_production_evaluation.json"
    )

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    # Failed evaluation must never replace production artifact.
    if not validation_passed:
        raise RuntimeError(
            "VALIDATION FAILED. Existing production artifact "
            "was NOT modified. Review evaluation report."
        )

    # --------------------------------------------------------
    # 6. FINAL MODEL - TRAIN ON ALL ELIGIBLE DATA
    # --------------------------------------------------------

    final_model = create_candidates(
        numeric_features,
        categorical_features
    )[best_name]

    final_model.fit(X, y)

    # --------------------------------------------------------
    # 7. BACKUP EXISTING ARTIFACTS
    # --------------------------------------------------------

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d_%H%M%S")

    for filename in ["model.joblib", "metadata.json"]:

        existing = ARTIFACT_DIR / filename

        if existing.exists():

            backup_path = (
                BACKUP_DIR / f"{timestamp}_{filename}"
            )

            shutil.copy2(existing, backup_path)

            logger.info("Backup created: %s", backup_path)

    # --------------------------------------------------------
    # 8. CREATE PRODUCTION METADATA
    # --------------------------------------------------------

    metadata = {
        "model_name": "seed_quantity",
        "status": "trained",
        "validation_status": "passed",
        "version": "2.0.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": best_name,
        "target_column": "ag4a_10_1",
        "target_unit": "KG",
        "unit_verified": True,
        "target_transformation": "none",
        "feature_columns": feature_columns,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "target_label_map": {},
        "metrics": {
            **test_metrics,
            "baseline_mae_kg": float(baseline_mae),
            "baseline_improvement_percent": float(improvement),
            "validation_status": "passed"
        },
        "cross_validation": cv_results,
        "data_audit": audit,
        "split_method": "GroupShuffleSplit by sdd_hhid",
        "training_rows": len(X),
        "testing_rows": len(X_test),
        "prediction_scale": "KG",
        "api_compatible": True
    }

    # --------------------------------------------------------
    # 9. ATOMIC ARTIFACT PUBLICATION
    # --------------------------------------------------------

    temp_model = ARTIFACT_DIR / "model.tmp.joblib"
    temp_metadata = ARTIFACT_DIR / "metadata.tmp.json"

    joblib.dump(final_model, temp_model)

    with temp_metadata.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)

    # Verify saved artifact before publication.
    verification_model = joblib.load(temp_model)

    if not hasattr(verification_model, "predict"):
        raise RuntimeError("Saved model failed verification.")

    if list(verification_model.feature_names_in_) != feature_columns:
        raise RuntimeError("Feature verification failed.")

    # Replace only after successful training and verification.
    temp_model.replace(ARTIFACT_DIR / "model.joblib")
    temp_metadata.replace(ARTIFACT_DIR / "metadata.json")

    logger.info("=" * 75)
    logger.info("PRODUCTION MODEL PUBLISHED")
    logger.info("Model: %s", ARTIFACT_DIR / "model.joblib")
    logger.info("Metadata: %s", ARTIFACT_DIR / "metadata.json")
    logger.info("Evaluation: %s", report_path)
    logger.info("Version: 2.0.0")
    logger.info("Prediction target: actual KG")
    logger.info("Raw dataset modified: NO")
    logger.info("Other models modified: NO")
    logger.info("=" * 75)


if __name__ == "__main__":
    main()
