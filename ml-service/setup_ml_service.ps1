# setup_ml_service.ps1 - inaunda faili zote za ml-service katika folda ya sasa
# Endesha ndani ya ml-service:  powershell -ExecutionPolicy Bypass -File .\setup_ml_service.ps1
$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding($false)   # UTF-8 bila BOM
function Write-File($rel, $content) {
  $path = Join-Path (Get-Location) $rel
  if (Test-Path $path) { Copy-Item $path "$path.old" -Force; Write-Host "Backup: $rel.old" }
  [System.IO.File]::WriteAllText($path, ($content -replace "`r`n","`n"), $utf8)
  Write-Host "Imeandikwa: $rel"
}
foreach ($d in @("ingestion","preprocessing","validation","models","data\raw\nbs","data\raw\nasa_power","data\raw\soilgrids","data\raw\sentinel2","data\processed","data\external_metadata")) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

Write-File 'requirements.txt' @'
fastapi==0.115.0
uvicorn==0.32.0
scikit-learn==1.5.2
pandas==2.2.3
numpy==2.1.1
joblib==1.4.2
requests==2.32.3
'@

Write-File 'Dockerfile' @'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
COPY models/ models/
# Hakuna mafunzo hapa. Modeli iliyothibitishwa (models/yield_model.pkl) lazima iwepo kabla ya build.
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'@

Write-File 'main.py' @'
"""AFIP ML Service - utabiri wa mavuno ya mahindi (modeli iliyofunzwa kwa data halisi)."""
import os
from contextlib import asynccontextmanager
from typing import Optional
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "yield_model.pkl")
bundle = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bundle
    if os.path.exists(MODEL_PATH):
        bundle = joblib.load(MODEL_PATH)
        print(f"Model loaded: {bundle['meta']['model_version']}", flush=True)
    else:
        print(f"WARNING: {MODEL_PATH} haipo. Endesha pipeline ya data halisi kisha train_model.py.", flush=True)
    yield

app = FastAPI(title="AFIP ML Service", version="2.0.0", lifespan=lifespan)

class YieldRequest(BaseModel):
    ndvi: float = Field(..., ge=-1.0, le=1.0)
    ph: Optional[float] = Field(None, ge=0.0, le=14.0)
    nitrogen: Optional[float] = Field(None, ge=0.0, description="g/kg")
    carbon: Optional[float] = Field(None, ge=0.0, description="g/kg")
    rainfall: Optional[float] = Field(None, ge=0.0, description="mm ya msimu")
    temperature: Optional[float] = Field(None, description="wastani wa C")

class YieldResponse(BaseModel):
    yield_t_ha: float
    interval_low: float
    interval_high: float
    confidence: Optional[float] = None
    model_version: str
    imputed_features: list[str]
    features_used: dict
    test_rmse: float

@app.get("/health")
def health():
    return {"status": "UP", "model_loaded": bundle is not None,
            "model_version": bundle["meta"]["model_version"] if bundle else None}

@app.get("/model-info")
def info():
    if bundle is None:
        raise HTTPException(503, "Model not loaded")
    return bundle["meta"]

@app.post("/predict", response_model=YieldResponse)
def predict(req: YieldRequest):
    if bundle is None:
        raise HTTPException(503, "Model not loaded")
    meta = bundle["meta"]
    feats = meta["features"]
    row = {f: getattr(req, f) for f in feats}
    imputed = [f for f, v in row.items() if v is None]
    pred = float(bundle["pipeline"].predict(pd.DataFrame([row], columns=feats))[0])
    lo_r, hi_r = meta["interval_residual_q10_q90"]
    return YieldResponse(
        yield_t_ha=round(max(pred, 0.0), 2),
        interval_low=round(max(pred + lo_r, 0.0), 2),
        interval_high=round(max(pred + hi_r, 0.0), 2),
        confidence=None,
        model_version=meta["model_version"],
        imputed_features=imputed,
        features_used={k: v for k, v in row.items() if v is not None},
        test_rmse=round(meta["test_metrics"]["rmse"], 3),
    )
'@

Write-File 'train_model.py' @'
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
'@

Write-File 'README.md' @'
# AFIP ml-service (data halisi pekee)

## Unachohitaji kuweka (siwezi kukutengenezea)
1. data/raw/nbs/yield_labels.csv  - mavuno HALISI ya mahindi (angalia yield_labels.TEMPLATE.csv)
   Safu: plot_id,region,latitude,longitude,year,yield_t_ha,source,collection_date
   Vyanzo: NBS Tanzania, World Bank LSMS-ISA (Tanzania National Panel Survey), data ya Wizara/utafiti.
   Chini ya safu 200 na mikoa 6 validation itakataa.
2. data/raw/sentinel2/ndvi.csv    - plot_id,year,ndvi_max (NDVI ya juu ya msimu kutoka Sentinel-2)
3. Faili ya chanzo/leseni kwenye data/external_metadata/

## Hatua
python -m venv .venv ; .venv\Scripts\activate ; pip install -r requirements.txt
python preprocessing\build_dataset.py --season-start-month 11 --season-end-month 5
python validation\validate_dataset.py
python train_model.py
uvicorn main:app --port 8000
Kisha jaribu: http://localhost:8000/health na /docs
'@

Write-File '.gitignore' @'
# Data ghafi ya NBS/World Bank hairuhusiwi kusambazwa
data/raw/
data/processed/
.venv/
__pycache__/
*.old
'@

Write-File 'ingestion\nasa_power.py' @'
"""Pakua mvua na joto la msimu kutoka NASA POWER (data halisi, inahifadhiwa raw)."""
import calendar, json, time
from pathlib import Path
import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "nasa_power"
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

def season_window(year, start_month, end_month):
    sy = year - 1 if start_month > end_month else year
    start = f"{sy}{start_month:02d}01"
    end = f"{year}{end_month:02d}{calendar.monthrange(year, end_month)[1]:02d}"
    return start, end

def fetch_season(lat, lon, year, start_month, end_month):
    start, end = season_window(year, start_month, end_month)
    RAW.mkdir(parents=True, exist_ok=True)
    f = RAW / f"{lat:.3f}_{lon:.3f}_{start}_{end}.json"
    if f.exists():
        j = json.loads(f.read_text())
    else:
        r = requests.get(URL, params={
            "parameters": "PRECTOTCORR,T2M", "community": "AG",
            "latitude": lat, "longitude": lon, "start": start, "end": end, "format": "JSON"},
            timeout=60)
        r.raise_for_status()
        j = r.json()
        f.write_text(json.dumps(j))
        time.sleep(0.5)
    p = j["properties"]["parameter"]
    rain = [v for v in p["PRECTOTCORR"].values() if v != -999]
    temp = [v for v in p["T2M"].values() if v != -999]
    if len(rain) < 0.8 * len(p["PRECTOTCORR"]):
        return None, None
    return round(sum(rain), 1), round(sum(temp) / len(temp), 2) if temp else None
'@

Write-File 'ingestion\soilgrids.py' @'
"""Pakua udongo (pH, nitrogen, kaboni) kutoka ISRIC SoilGrids, wastani wa kina 0-30 cm.
Kumbuka: SoilGrids ina kikomo ~5 maombi kwa dakika; ndiyo maana kuna sleep."""
import json, time
from pathlib import Path
import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "soilgrids"
URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
MAP = {"phh2o": "ph", "nitrogen": "nitrogen", "soc": "carbon"}   # baada ya d_factor: pH, g/kg, g/kg

def fetch_soil(lat, lon):
    RAW.mkdir(parents=True, exist_ok=True)
    f = RAW / f"{lat:.4f}_{lon:.4f}.json"
    if f.exists():
        j = json.loads(f.read_text())
    else:
        params = [("lon", lon), ("lat", lat), ("value", "mean")]
        params += [("property", p) for p in MAP]
        params += [("depth", d) for d in ("0-5cm", "5-15cm", "15-30cm")]
        r = requests.get(URL, params=params, timeout=90)
        r.raise_for_status()
        j = r.json()
        f.write_text(json.dumps(j))
        time.sleep(13)
    out = {}
    for layer in j["properties"]["layers"]:
        name = layer["name"]
        if name not in MAP:
            continue
        d = layer["unit_measure"]["d_factor"]
        vals = [x["values"]["mean"] for x in layer["depths"] if x["values"].get("mean") is not None]
        out[MAP[name]] = round(sum(vals) / len(vals) / d, 3) if vals else None
    return out
'@

Write-File 'ingestion\nps_variables.py' @'
"""Tafuta majina ya faili na variables za utafiti wa NPS kupitia NADA API (metadata tu, hakuna microdata)."""
import sys
import requests

BASE = "https://microdata.worldbank.org/index.php/api"   # ikishindwa (404), ondoa "/index.php"
STUDY = "TZA_2019_NPS-SDD_v06_M"                          # 2008/09: TZA_2008_NPS-R1_v03_M, 2010/11: TZA_2010_NPS-R2_v03_M

def get(path, **params):
    r = requests.get(BASE + path, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

print(get(f"/catalog/{STUDY}/data_files"))
for kw in sys.argv[1:] or ["harvest", "plot area", "maize", "GPS"]:
    res = get(f"/catalog/{STUDY}/variables", sk=kw, ps=50)
    for v in res.get("variables", []):
        print(f"{kw:10} | {v.get('file_id')} | {v.get('name')} - {v.get('labl')}")
'@

Write-File 'preprocessing\build_dataset.py' @'
"""Unganisha labels halisi za mavuno na vipengele halisi (NASA POWER, SoilGrids, NDVI).
Pembejeo:
  data/raw/nbs/yield_labels.csv   (plot_id,region,latitude,longitude,year,yield_t_ha,source,collection_date)
  data/raw/sentinel2/ndvi.csv     (plot_id,year,ndvi_max)
Matokeo: data/processed/yield_dataset.csv"""
import argparse, json, sys
from datetime import date
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ingestion"))
from nasa_power import fetch_season
from soilgrids import fetch_soil

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season-start-month", type=int, required=True, help="mf. 11 (Novemba)")
    ap.add_argument("--season-end-month", type=int, required=True, help="mf. 5 (Mei)")
    a = ap.parse_args()

    lab = ROOT / "data/raw/nbs/yield_labels.csv"
    ndv = ROOT / "data/raw/sentinel2/ndvi.csv"
    for p in (lab, ndv):
        if not p.exists():
            sys.exit(f"HAIPO: {p}. Weka data halisi kwanza (angalia README).")
    labels = pd.read_csv(lab)
    ndvi = pd.read_csv(ndv)[["plot_id", "year", "ndvi_max"]].rename(columns={"ndvi_max": "ndvi"})
    df = labels.merge(ndvi, on=["plot_id", "year"], how="left")

    rows = []
    for i, r in df.iterrows():
        rain, temp = fetch_season(r.latitude, r.longitude, int(r.year), a.season_start_month, a.season_end_month)
        soil = fetch_soil(r.latitude, r.longitude)
        rows.append({"rainfall": rain, "temperature": temp,
                     "ph": soil.get("ph"), "nitrogen": soil.get("nitrogen"), "carbon": soil.get("carbon")})
        print(f"{i+1}/{len(df)} {r.plot_id}", flush=True)
    out = pd.concat([df, pd.DataFrame(rows)], axis=1)
    cols = ["plot_id", "region", "year", "latitude", "longitude", "ndvi", "ph", "nitrogen", "carbon",
            "rainfall", "temperature", "yield_t_ha", "source", "collection_date"]
    out = out[cols]
    dest = ROOT / "data/processed/yield_dataset.csv"
    out.to_csv(dest, index=False)
    (ROOT / "data/external_metadata/dataset_build.json").write_text(json.dumps({
        "built_on": date.today().isoformat(), "rows": len(out),
        "season_months": [a.season_start_month, a.season_end_month],
        "sources": ["labels: " + lab.name, "NASA POWER daily", "ISRIC SoilGrids v2.0", "NDVI: " + ndv.name]
    }, indent=2))
    print(f"Imeandikwa {dest} ({len(out)} safu). Endesha validation/validate_dataset.py")

if __name__ == "__main__":
    main()
'@

Write-File 'validation\validate_dataset.py' @'
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
'@

Write-File 'data\raw\nbs\yield_labels.TEMPLATE.csv' @'
plot_id,region,latitude,longitude,year,yield_t_ha,source,collection_date
'@

Write-File 'data\external_metadata\README_SOURCES.txt' @'
Kwa kila chanzo cha data andika faili <chanzo>.json hapa chenye:
{"source": "...", "url": "...", "license": "...", "collected_on": "YYYY-MM-DD", "level": "plot|district|region", "notes": "..."}
'@

Write-Host "`nTAYARI. Hatua inayofuata: python -m venv .venv ; .venv\Scripts\Activate.ps1 ; pip install -r requirements.txt"
