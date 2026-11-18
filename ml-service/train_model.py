"""Mafunzo kwa data halisi PEKEE. Inakataa kuendesha ikiwa validation imeshindwa."""
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "validation"))
from validate_dataset import DATASET, validate

FEATURES = ["ndvi", "ph", "nitrogen", "carbon", "rainfall", "temperature"]

def metrics(y, p):
    return {"rmse": float(np.sqrt(mean_squared_error(y, p))), "mae": float(mean_absolute_error(y, p)),
            "r2": float(r2_score(y, p))}

def main():
    rep = validate()
    if not rep["ok"]:
        sys.exit("MAFUNZO YAMEZUIWA (DATA_POLICY): " + "; ".join(rep["errors"]))
    df = pd.read_csv(DATASET)
    X, y, g = df[FEATURES], df["yield_t_ha"], df["region"]

    # Gawa kwa MKOA ili kuzuia uvujaji wa data kati ya train/val/test
    s1 = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    tv, te = next(s1.split(X, y, g))
    s2 = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    tr_i, va_i = next(s2.split(X.iloc[tv], y.iloc[tv], g.iloc[tv]))
    tr, va = tv[tr_i], tv[va_i]

    candidates = {
        "random-forest": RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=42, n_jobs=-1),
        "gradient-boosting": GradientBoostingRegressor(random_state=42),
    }
    best_name, best_pipe, best_rmse = None, None, 1e9
    for name, est in candidates.items():
        pipe = Pipeline([("imp", SimpleImputer(strategy="median")), ("m", est)]).fit(X.iloc[tr], y.iloc[tr])
        m = metrics(y.iloc[va], pipe.predict(X.iloc[va]))
        print(name, "validation:", m)
        if m["rmse"] < best_rmse:
            best_name, best_pipe, best_rmse = name, pipe, m["rmse"]

    resid = y.iloc[va].values - best_pipe.predict(X.iloc[va])
    q_lo, q_hi = float(np.quantile(resid, 0.1)), float(np.quantile(resid, 0.9))
    test_m = metrics(y.iloc[te], best_pipe.predict(X.iloc[te]))
    baseline = metrics(y.iloc[te], np.full(len(te), y.iloc[tr].mean()))
    print("TEST:", test_m, "| baseline (wastani):", baseline)

    digest = hashlib.sha256(DATASET.read_bytes()).hexdigest()[:12]
    version = f"{best_name}-{datetime.now(timezone.utc):%Y%m%d}-{digest}"
    meta = {"model_version": version, "algorithm": best_name, "features": FEATURES,
            "trained_at": datetime.now(timezone.utc).isoformat(), "dataset_sha256_12": digest,
            "rows": {"train": len(tr), "val": len(va), "test": len(te)},
            "test_metrics": test_m, "baseline_test_metrics": baseline,
            "interval_residual_q10_q90": [q_lo, q_hi],
            "test_regions": sorted(g.iloc[te].unique().tolist())}
    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump({"pipeline": best_pipe, "meta": meta}, ROOT / "models" / "yield_model.pkl")
    (ROOT / "models" / "model_metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    if test_m["rmse"] >= baseline["rmse"]:
        print("ONYO: modeli haishindi utabiri wa wastani. Usiitumie bila kuboresha data.")
    print("Imehifadhi models/yield_model.pkl")

if __name__ == "__main__":
    main()