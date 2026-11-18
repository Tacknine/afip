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