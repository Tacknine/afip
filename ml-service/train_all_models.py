import json
import logging
import warnings
from pathlib import Path
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")

# ============================================================
# AFIP - AGRICULTURAL FORECASTING AND INTELLIGENCE PLATFORM
# MODEL TRAINING PIPELINE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

RAW_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "nbs"
    / "nps2019"
    / "TZA_2019_NPD-SDD_v06_M_STATA12"
)

ARTIFACTS_DIR = BASE_DIR / "artifacts"
REPORTS_DIR = BASE_DIR / "reports"

ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = REPORTS_DIR / "training.log"
REPORT_FILE = REPORTS_DIR / "training_report.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AFIP")


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_CONFIG = {
    "seed_quantity": {
        "status": "pending",
        "target": "ag4a_10_1",
        "unit_column": "ag4a_10_2",
        "required_unit_code": 1,
        "target_unit": "KG",
        "reason": None
    },

    "maize_yield": {
        "status": "blocked",
        "reason": (
            "Harvest quantity unit has not been verified "
            "from the official questionnaire or data dictionary."
        )
    },

    "crop_recommendation": {
        "status": "blocked",
        "reason": (
            "Official crop-code mapping and recommendation "
            "target design are still required."
        )
    },

    "crop_production": {
        "status": "blocked",
        "reason": (
            "Harvest quantity unit has not been verified."
        )
    }
}


# ============================================================
# DATASET DISCOVERY
# ============================================================

def find_dataset(filename):

    matches = list(RAW_DIR.rglob(filename))

    if not matches:
        raise FileNotFoundError(
            f"Dataset not found: {filename}\n"
            f"Search directory: {RAW_DIR}"
        )

    if len(matches) > 1:
        logger.warning(
            "Multiple files found for %s. Using: %s",
            filename,
            matches[0]
        )

    return matches[0]


def load_stata(filename):

    path = find_dataset(filename)

    logger.info("Loading dataset: %s", path.name)

    df = pd.read_stata(
        path,
        convert_categoricals=False
    )

    logger.info(
        "Loaded %s: rows=%s columns=%s",
        filename,
        len(df),
        len(df.columns)
    )

    return df


# ============================================================
# SEED QUANTITY DATA PREPARATION
# ============================================================

def prepare_seed_quantity_data():

    df = load_stata("AG_SEC_4A.dta")

    required_columns = [
        "sdd_hhid",
        "cropid",
        "ag4a_01",
        "ag4a_02",
        "ag4a_04",
        "ag4a_06",
        "ag4a_08",
        "ag4a_10_1",
        "ag4a_10_2"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Required columns missing: {missing}"
        )

    original_rows = len(df)

    # Only KG records are eligible.
    df["ag4a_10_2"] = pd.to_numeric(
        df["ag4a_10_2"],
        errors="coerce"
    )

    df["ag4a_10_1"] = pd.to_numeric(
        df["ag4a_10_1"],
        errors="coerce"
    )

    df = df[
        df["ag4a_10_2"] == 1
    ].copy()

    # Exclude missing, zero, negative and infinite targets.
    df = df[
        np.isfinite(df["ag4a_10_1"])
        & (df["ag4a_10_1"] > 0)
    ].copy()

    # Household identifier is used only for grouped splitting.
    df["sdd_hhid"] = df["sdd_hhid"].astype(str)

    df = df[
        df["sdd_hhid"].notna()
        & (df["sdd_hhid"] != "")
        & (df["sdd_hhid"] != "nan")
    ].copy()

    feature_columns = [
        "cropid",
        "ag4a_01",
        "ag4a_02",
        "ag4a_04",
        "ag4a_06",
        "ag4a_08"
    ]

    X = df[feature_columns].copy()
    y = df["ag4a_10_1"].copy()
    groups = df["sdd_hhid"].copy()

    # Numeric and categorical feature handling.
    numeric_features = [
        "ag4a_02"
    ]

    categorical_features = [
        "cropid",
        "ag4a_01",
        "ag4a_04",
        "ag4a_06",
        "ag4a_08"
    ]

    # Convert numeric feature safely.
    for col in numeric_features:
        X[col] = pd.to_numeric(
            X[col],
            errors="coerce"
        )

    # Convert categorical features to strings.
    for col in categorical_features:
        X[col] = X[col].apply(
            lambda value: (
                str(value)
                if pd.notna(value)
                else np.nan
            )
        )

    # Remove features with no usable values.
    usable_features = [
        col for col in feature_columns
        if X[col].notna().any()
    ]

    X = X[usable_features]

    numeric_features = [
        col for col in numeric_features
        if col in usable_features
    ]

    categorical_features = [
        col for col in categorical_features
        if col in usable_features
    ]

    logger.info("Seed quantity data audit")
    logger.info("Original rows: %s", original_rows)
    logger.info("KG records with valid positive targets: %s", len(df))
    logger.info("Unique households: %s", groups.nunique())
    logger.info("Features: %s", usable_features)

    audit = {
        "original_rows": int(original_rows),
        "eligible_rows": int(len(df)),
        "unique_households": int(groups.nunique()),
        "target": "ag4a_10_1",
        "target_unit": "KG",
        "unit_filter": "ag4a_10_2 == 1",
        "feature_columns": usable_features
    }

    return (
        X,
        y,
        groups,
        numeric_features,
        categorical_features,
        audit
    )


# ============================================================
# SEED QUANTITY MODEL TRAINING
# ============================================================

def train_seed_quantity():

    logger.info("=" * 70)
    logger.info("TRAINING SEED QUANTITY MODEL")
    logger.info("=" * 70)

    (
        X,
        y,
        groups,
        numeric_features,
        categorical_features,
        audit
    ) = prepare_seed_quantity_data()

    if len(X) < 50:
        raise ValueError(
            f"Insufficient training records: {len(X)}. "
            "At least 50 eligible records are required."
        )

    if groups.nunique() < 5:
        raise ValueError(
            "Insufficient unique households for grouped validation."
        )

    # Household-based split prevents the same household
    # from appearing in both training and testing sets.
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=42
    )

    train_indices, test_indices = next(
        splitter.split(X, y, groups=groups)
    )

    X_train = X.iloc[train_indices]
    X_test = X.iloc[test_indices]

    y_train = y.iloc[train_indices]
    y_test = y.iloc[test_indices]

    logger.info("Training rows: %s", len(X_train))
    logger.info("Testing rows: %s", len(X_test))

    if len(X_test) < 20:
        raise ValueError(
            "Testing dataset has fewer than 20 records."
        )

    transformers = []

    if numeric_features:
        numeric_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(strategy="median")
                )
            ]
        )

        transformers.append(
            (
                "numeric",
                numeric_pipeline,
                numeric_features
            )
        )

    if categorical_features:
        categorical_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(strategy="most_frequent")
                ),
                (
                    "encoder",
                    OneHotEncoder(handle_unknown="ignore")
                )
            ]
        )

        transformers.append(
            (
                "categorical",
                categorical_pipeline,
                categorical_features
            )
        )

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop"
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=300,
                    max_depth=15,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
            )
        ]
    )

    # Log transformation helps reduce the influence
    # of highly skewed seed quantities.
    y_train_log = np.log1p(y_train)

    model.fit(
        X_train,
        y_train_log
    )

    predictions_log = model.predict(X_test)

    predictions = np.expm1(predictions_log)
    predictions = np.maximum(predictions, 0)

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    r2 = r2_score(
        y_test,
        predictions
    )

    # Baseline: always predict training-set median.
    baseline_prediction = np.full(
        len(y_test),
        float(y_train.median())
    )

    baseline_mae = mean_absolute_error(
        y_test,
        baseline_prediction
    )

    # Do not publish a model as validated unless it
    # performs better than the simple baseline.
    validation_passed = (
        np.isfinite(mae)
        and np.isfinite(rmse)
        and mae < baseline_mae
    )

    metrics = {
        "mae_kg": float(mae),
        "rmse_kg": float(rmse),
        "r2": float(r2),
        "baseline_mae_kg": float(baseline_mae),
        "test_records": int(len(y_test)),
        "train_records": int(len(y_train)),
        "households_total": int(groups.nunique()),
        "validation_status": (
            "passed"
            if validation_passed
            else "failed"
        )
    }

    logger.info("MODEL EVALUATION")
    logger.info("MAE: %.4f KG", mae)
    logger.info("RMSE: %.4f KG", rmse)
    logger.info("R2: %.4f", r2)
    logger.info("Baseline MAE: %.4f KG", baseline_mae)
    logger.info("Validation: %s", metrics["validation_status"])

    # Save only a model that passes validation.
    if not validation_passed:
        raise RuntimeError(
            "Seed quantity model did not outperform "
            "the baseline. Model was NOT published."
        )

    artifact_dir = ARTIFACTS_DIR / "seed_quantity"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    model_path = artifact_dir / "model.joblib"
    metadata_path = artifact_dir / "metadata.json"

    joblib.dump(
        model,
        model_path
    )

    metadata = {
        "model_name": "seed_quantity",
        "status": "trained",
        "validation_status": "passed",
        "version": "1.0.0",
        "trained_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "target_column": "ag4a_10_1",
        "target_unit": "KG",
        "unit_verified": True,
        "feature_columns": list(X.columns),
        "target_label_map": {},
        "metrics": metrics,
        "data_audit": audit,
        "split_method": "GroupShuffleSplit by sdd_hhid",
        "training_rows": int(len(X_train)),
        "testing_rows": int(len(X_test))
    }

    with open(
        metadata_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
            ensure_ascii=False
        )

    logger.info("Model saved: %s", model_path)
    logger.info("Metadata saved: %s", metadata_path)

    return {
        "status": "trained",
        "validation_status": "passed",
        "metrics": metrics,
        "model_path": str(model_path),
        "metadata_path": str(metadata_path)
    }


# ============================================================
# MAIN TRAINING PIPELINE
# ============================================================

def main():

    report = {
        "platform": "AFIP",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "raw_data_modified": False,
        "models": {}
    }

    logger.info("=" * 70)
    logger.info("AFIP MODEL TRAINING PIPELINE")
    logger.info("=" * 70)

    # Seed quantity model.
    try:
        report["models"]["seed_quantity"] = (
            train_seed_quantity()
        )

    except Exception as error:
        logger.exception(
            "Seed quantity training failed."
        )

        report["models"]["seed_quantity"] = {
            "status": "failed",
            "reason": str(error)
        }

    # Other models remain blocked until their
    # data requirements have been verified.
    for model_name in [
        "maize_yield",
        "crop_recommendation",
        "crop_production"
    ]:
        report["models"][model_name] = {
            "status": MODEL_CONFIG[model_name]["status"],
            "reason": MODEL_CONFIG[model_name]["reason"]
        }

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    logger.info("=" * 70)
    logger.info("AFIP TRAINING SUMMARY")
    logger.info("=" * 70)

    for name, result in report["models"].items():
        logger.info(
            "%s: %s",
            name.upper(),
            result["status"].upper()
        )

    logger.info("Training report: %s", REPORT_FILE)
    logger.info("Raw datasets were not modified.")
    logger.info("TRAINING PIPELINE COMPLETED.")


if __name__ == "__main__":
    main()
