import sys, requests
BASE = "https://microdata.worldbank.org/index.php/api"
STUDY = "TZA_2019_NPS-SDD_v06_M"
for fid in sys.argv[1:] or ["F39", "F42", "F43"]:
    r = requests.get(f"{BASE}/catalog/{STUDY}/data_files/{fid}/variables", timeout=60)
    r.raise_for_status()
    j = r.json()
    rows = j.get("variables", j) if isinstance(j, dict) else j
    if isinstance(rows, dict):
        rows = list(rows.values())
    print("=====", fid)
    for v in rows:
        print(v.get("name"), "-", v.get("labl"))
