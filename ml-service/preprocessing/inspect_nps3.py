"""Thibitisha msimbo wa zao na hesabu mashamba kwa mkoa. Muhtasari tu."""
import sys
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1] / "data" / "raw" / "nbs"
BASE = "https://microdata.worldbank.org/index.php/api"
STUDY = "TZA_2019_NPS-SDD_v06_M"
CODE = sys.argv[1] if len(sys.argv) > 1 else "1"
num = lambda s: pd.to_numeric(s, errors="coerce")

def path_of(name):
    hits = [p for p in ROOT.rglob("*.dta") if p.stem.lower() == name.lower()]
    return hits[0] if hits else None

def read(name):
    p = path_of(name)
    if p is None:
        sys.exit(f"{name}.dta haipo")
    return pd.read_stata(p, convert_categoricals=True)

print("===== Lebo za cropid kwenye .dta")
try:
    with pd.read_stata(path_of("AG_SEC_4A"), iterator=True) as r:
        tabs = r.value_labels()
    found = False
    for t, m in tabs.items():
        if any("maize" in str(v).lower() for v in m.values()):
            found = True
            print(f"  jedwali '{t}':", {int(k): v for k, v in sorted(m.items()) if int(k) <= 40})
    if not found:
        print("  hakuna lebo za maandishi ndani ya .dta")
except Exception as e:
    print("  imeshindwa kusoma lebo:", e)

print("\n===== Lebo za cropid kutoka API ya katalogi")
try:
    f = requests.get(f"{BASE}/catalog/{STUDY}/data_files/F42/variables", timeout=60).json()
    rows = f.get("variables", f) if isinstance(f, dict) else f
    rows = list(rows.values()) if isinstance(rows, dict) else rows
    vid = next(v.get("vid") for v in rows if v.get("name") == "cropid")
    d = requests.get(f"{BASE}/catalog/{STUDY}/variables/{vid}", timeout=60).json()
    cats = d.get("var_catgry") or d.get("variable", {}).get("var_catgry") or []
    print("  ", [(c.get("value"), c.get("labl")) for c in cats][:60] or "hakuna lebo kwenye API")
except Exception as e:
    print("  API imeshindwa:", e)

print(f"\n===== Mashamba ya zao msimbo {CODE}, kwa mkoa (hayajachanganywa na zao lingine)")
hh = read("HH_SEC_A")[["sdd_hhid", "t0_region", "t0_district"]]
parts = []
for nm, p, q in [("AG_SEC_4A", "ag4a", "ag4a_27"), ("AG_SEC_4B", "ag4b", "ag4b_28")]:
    d = read(nm)
    d = d[d["cropid"].astype(str) == CODE].copy()
    d["qty"], d["area"] = num(d[q]), num(d[f"{p}_21"])
    d["inter"] = d[f"{p}_04"].astype(str).str.upper()
    d["season"] = nm
    parts.append(d[["sdd_hhid", "plotnum", "season", "qty", "area", "inter"]])
m = pd.concat(parts).merge(hh, on="sdd_hhid", how="left")
ok = (m.qty > 0) & (m.area > 0)
clean = m[ok & (m.inter == "NO")]
print("  safu zote za zao hili:", len(m), "| kiasi>0 na eneo>0:", int(ok.sum()), "| na bila mchanganyiko:", len(clean))
bc = clean["t0_region"].astype(str).value_counts()
print("  kwa mkoa:", {k: int(v) for k, v in bc.items()})
print("  mikoa yenye >=10:", int((bc >= 10).sum()), "| wilaya kwa mashamba >=5:", int((clean["t0_district"].astype(str).value_counts() >= 5).sum()))


