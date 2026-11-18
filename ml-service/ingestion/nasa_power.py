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