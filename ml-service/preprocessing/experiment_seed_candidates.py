import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor
)
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error, mean_squared_error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from train_all_models import prepare_seed_quantity_data


# ==========================================================
# AFIP SEED QUANTITY - CANDIDATE MODEL EXPERIMENT
# ==========================================================

X, y, groups, numeric, categorical, audit = prepare_seed_quantity_data()

X = X.reset_index(drop=True)
y = pd.Series(y).reset_index(drop=True)
groups = pd.Series(groups).reset_index(drop=True)

print("=" * 85)
print("AFIP SEED QUANTITY - 5 FOLD MODEL EXPERIMENT")
print("=" * 85)

print("Records:", len(X))
print("Households:", groups.nunique())
print("Features:", list(X.columns))

# ----------------------------------------------------------
# MODELS
# ----------------------------------------------------------

models = {
    "RandomForest_Log": RandomForestRegressor(
        n_estimators=500,
        max_depth=12,
        min_samples_split=8,
        min_samples_leaf=4,
        max_features=0.8,
        random_state=42,
        n_jobs=-1
    ),

    "ExtraTrees_Log": ExtraTreesRegressor(
        n_estimators=500,
        max_depth=12,
        min_samples_split=8,
        min_samples_leaf=4,
        max_features=0.8,
        random_state=42,
        n_jobs=-1
    ),

    "GradientBoosting_Log": GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.03,
        max_depth=2,
        min_samples_leaf=5,
        loss="huber",
        random_state=42
    )
}

# ----------------------------------------------------------
# PREPROCESSOR
# ----------------------------------------------------------

def build_preprocessor():

    transformers = []

    if numeric:
        transformers.append((
            "numeric",
            SimpleImputer(strategy="median"),
            numeric
        ))

    if categorical:
        transformers.append((
            "categorical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore"))
            ]),
            categorical
        ))

    return ColumnTransformer(transformers)


def build_model(estimator):

    pipeline = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("regressor", estimator)
    ])

    return TransformedTargetRegressor(
        regressor=pipeline,
        func=np.log1p,
        inverse_func=np.expm1
    )


# ----------------------------------------------------------
# GROUP CROSS VALIDATION
# ----------------------------------------------------------

cv = GroupKFold(n_splits=5)

predictions = {
    name: np.full(len(X), np.nan)
    for name in models
}

predictions["Global_Median"] = np.full(len(X), np.nan)
predictions["Crop_Median"] = np.full(len(X), np.nan)

for fold, (train_idx, test_idx) in enumerate(
    cv.split(X, y, groups), start=1
):

    print(f"\nPROCESSING FOLD {fold}/5")

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]

    global_median = float(y_train.median())

    train_data = X_train.copy()
    train_data["target"] = y_train.to_numpy()

    crop_medians = train_data.groupby(
        "cropid"
    )["target"].median()

    predictions["Global_Median"][test_idx] = global_median

    predictions["Crop_Median"][test_idx] = (
        X_test["cropid"]
        .map(crop_medians)
        .fillna(global_median)
        .to_numpy(dtype=float)
    )

    for name, estimator in models.items():

        candidate = build_model(estimator)

        candidate.fit(X_train, y_train)

        predicted = candidate.predict(X_test)

        predictions[name][test_idx] = np.maximum(
            predicted, 0
        )

        print(f"  Completed: {name}")


# ----------------------------------------------------------
# OVERALL EVALUATION
# ----------------------------------------------------------

print("\n" + "=" * 85)
print("OVERALL OUT-OF-FOLD RESULTS")
print("=" * 85)

results = []

for name, predicted in predictions.items():

    mae = mean_absolute_error(y, predicted)

    rmse = np.sqrt(
        mean_squared_error(y, predicted)
    )

    results.append({
        "model": name,
        "MAE_KG": mae,
        "RMSE_KG": rmse
    })

    print(
        f"{name:<25} "
        f"MAE={mae:>10.4f} KG | "
        f"RMSE={rmse:>10.4f} KG"
    )

comparison = pd.DataFrame(results).sort_values("MAE_KG")

# ----------------------------------------------------------
# PER-CROP EVALUATION
# ----------------------------------------------------------

print("\n" + "=" * 85)
print("PER-CROP OUT-OF-FOLD PERFORMANCE")
print("=" * 85)

details = X[["cropid"]].copy()
details["actual_kg"] = y.to_numpy()

for name, predicted in predictions.items():
    details[name + "_error"] = np.abs(
        y.to_numpy() - predicted
    )

error_columns = [
    name + "_error" for name in predictions
]

crop_summary = details.groupby("cropid").agg(
    records=("actual_kg", "size"),
    actual_median=("actual_kg", "median"),
    **{
        column.replace("_error", "_MAE"): (column, "mean")
        for column in error_columns
    }
)

print(crop_summary.to_string())

# ----------------------------------------------------------
# SAVE EXPERIMENT RESULTS
# ----------------------------------------------------------

output = Path("audit_results")
output.mkdir(parents=True, exist_ok=True)

comparison.to_csv(
    output / "seed_candidate_comparison.csv",
    index=False
)

crop_summary.to_csv(
    output / "seed_candidate_per_crop.csv"
)

print("\n" + "=" * 85)
print("EXPERIMENT COMPLETED")
print("=" * 85)

print("Best candidate:", comparison.iloc[0]["model"])
print("Best MAE:", comparison.iloc[0]["MAE_KG"])

print("\nSaved:")
print(output / "seed_candidate_comparison.csv")
print(output / "seed_candidate_per_crop.csv")

print("\nRAW DATA WAS NOT MODIFIED.")
print("EXISTING MODEL ARTIFACTS WERE NOT MODIFIED.")
print("NO PRODUCTION MODEL WAS REPLACED.")

