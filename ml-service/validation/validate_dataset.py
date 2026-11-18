"""Kagua dataset kabla ya mafunzo. Inatoka na code 1 ikiwa kuna makosa."""
import json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/processed/yield_dataset.csv"
REPORT = ROOT / "validation/validation_report.json"
REQUIRED = ["plot_id", "region", "year", "latitude", "longitude", "ndvi", "ph", "nitrogen", "carbon",
            "rainfall", "temperature", "yield_t_ha", "source", "collection_date"]
RANGES = {"latitude": (-11.8, -0.9), "longitude": (29.3, 40.5), "ndvi": (-1, 1), "ph": (3, 10),
          "nitrogen": (0, 20), "carbon": (0, 200), "rainfall": (0, 3500), "temperature": (5, 40),
          "yield_t_ha": (0, 12)}
MIN_ROWS, MIN_REGIONS = 200, 6

def validate(path=DATASET):
    err, warn = [], []
    if not Path(path).exists():
        return {"ok": False, "errors": [f"Dataset haipo: {path}"], "warnings": [], "missing": {}}
    df = pd.read_csv(path)
    miss = [c for c in REQUIRED if c not in df.columns]
    if miss:
        return {"ok": False, "errors": [f"Safu zinazokosekana: {miss}"], "warnings": [], "missing": {}}
    if len(df) < MIN_ROWS: err.append(f"Safu {len(df)} < {MIN_ROWS} (data haitoshi)")
    if df.region.nunique() < MIN_REGIONS: err.append(f"Mikoa {df.region.nunique()} < {MIN_REGIONS}")
    for c in ("source", "collection_date", "yield_t_ha", "ndvi", "region"):
        if df[c].isna().any(): err.append(f"'{c}' ina thamani zinazokosekana")
    if df.duplicated(["plot_id", "year"]).any(): err.append("Kuna marudio ya plot_id+year")
    for c, (lo, hi) in RANGES.items():
        bad = df[c].dropna()
        n = int(((bad < lo) | (bad > hi)).sum())
        if n: err.append(f"'{c}': {n} thamani nje ya [{lo}, {hi}]")
    if (df.yield_t_ha <= 0).any(): err.append("Mavuno <= 0 yamegunduliwa")
    missing = {c: round(float(df[c].isna().mean()), 3) for c in REQUIRED}
    for c in ("ph", "nitrogen", "carbon", "rainfall", "temperature"):
        if missing[c] > 0.3: err.append(f"'{c}' ina >30% missing")
        elif missing[c] > 0: warn.append(f"'{c}' ina {missing[c]*100:.1f}% missing")
    rep = {"ok": not err, "rows": len(df), "regions": int(df.region.nunique()),
           "errors": err, "warnings": warn, "missing": missing}
    REPORT.write_text(json.dumps(rep, indent=2, ensure_ascii=False))
    return rep

if __name__ == "__main__":
    r = validate()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    sys.exit(0 if r["ok"] else 1)