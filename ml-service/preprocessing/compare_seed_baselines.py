import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error

from train_all_models import prepare_seed_quantity_data


X, y, groups, numeric, categorical, audit = prepare_seed_quantity_data()

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

# ------------------------------------------------
# BASELINE 1: GLOBAL MEDIAN
# ------------------------------------------------

global_median = float(y_train.median())

global_predictions = np.full(
    len(y_test),
    global_median
)

# ------------------------------------------------
# BASELINE 2: MEDIAN PER CROP
# ------------------------------------------------

train_frame = X_train.copy()
train_frame["target_kg"] = y_train

crop_medians = train_frame.groupby(
    "cropid"
)["target_kg"].median()

crop_predictions = (
    X_test["cropid"]
    .map(crop_medians)
    .fillna(global_median)
    .to_numpy(dtype=float)
)

# ------------------------------------------------
# RANDOM FOREST
# ------------------------------------------------

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

preprocessor = ColumnTransformer(transformers)

model = Pipeline([
    ("preprocessor", preprocessor),
    ("regressor", RandomForestRegressor(
        n_estimators=500,
        max_depth=12,
        min_samples_split=8,
        min_samples_leaf=4,
        max_features=0.8,
        random_state=42,
        n_jobs=-1
    ))
])

model.fit(X_train, y_train)

rf_predictions = np.maximum(
    model.predict(X_test),
    0
)


def evaluate(name, actual, predicted):

    mae = mean_absolute_error(actual, predicted)

    rmse = np.sqrt(
        mean_squared_error(actual, predicted)
    )

    print(
        f"{name:<25} "
        f"MAE={mae:>9.4f} KG | "
        f"RMSE={rmse:>9.4f} KG"
    )


print("\n" + "=" * 75)
print("AFIP - BASELINE COMPARISON")
print("=" * 75)

evaluate("Global median", y_test, global_predictions)
evaluate("Crop-specific median", y_test, crop_predictions)
evaluate("Random Forest", y_test, rf_predictions)

# ------------------------------------------------
# PER-CROP TEST PERFORMANCE
# ------------------------------------------------

results = X_test.copy()

results["actual_kg"] = y_test.to_numpy()
results["global_prediction"] = global_predictions
results["crop_median_prediction"] = crop_predictions
results["rf_prediction"] = rf_predictions

results["global_error"] = abs(
    results["actual_kg"] - results["global_prediction"]
)

results["crop_median_error"] = abs(
    results["actual_kg"] - results["crop_median_prediction"]
)

results["rf_error"] = abs(
    results["actual_kg"] - results["rf_prediction"]
)

print("\nPER-CROP TEST PERFORMANCE")

summary = results.groupby("cropid").agg(
    records=("actual_kg", "size"),
    actual_median=("actual_kg", "median"),
    global_mae=("global_error", "mean"),
    crop_median_mae=("crop_median_error", "mean"),
    random_forest_mae=("rf_error", "mean")
)

print(summary.sort_values("records", ascending=False).to_string())

print("\nMISSING VALUE AUDIT")
print("ag4a_02 training missing:", X_train["ag4a_02"].isna().sum())
print("ag4a_02 testing missing:", X_test["ag4a_02"].isna().sum())

print("\nHOUSEHOLD OVERLAP:")
print(
    len(
        set(groups.iloc[train_idx])
        .intersection(set(groups.iloc[test_idx]))
    )
)

print("\nBASELINE COMPARISON COMPLETED.")
print("RAW DATA WAS NOT MODIFIED.")
print("MODEL ARTIFACTS WERE NOT MODIFIED.")
