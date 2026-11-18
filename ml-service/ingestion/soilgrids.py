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