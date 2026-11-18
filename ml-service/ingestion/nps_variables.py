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