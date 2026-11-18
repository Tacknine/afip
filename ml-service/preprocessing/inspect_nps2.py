"""Ukaguzi wa pili wa NPS: msimbo wa mahindi, mavuno ya kadirio, tarehe za mahojiano, mikoa. Muhtasari tu."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "data" / "raw" / "nbs"
num = lambda s: pd.to_numeric(s, errors="coerce")

def load(name):
    hits = [p for p in ROOT.rglob("*.dta") if p.stem.lower() == name.lower()]
    if not hits:
        print(f"!! {name}.dta haipo"); return None
    try:
        return pd.read_stata(hits[0])
    except Exception:
        return pd.read_stata(hits[0], convert_categoricals=False)

for name, p in [("AG_SEC_4A", "ag4a"), ("AG_SEC_4B", "ag4b")]:
    df = load(name)
    if df is None:
        continue
    q = "ag4a_27" if p == "ag4a" else "ag4b_28"
    a, ic = f"{p}_21", f"{p}_04"
    print(f"\n===== {name}  (safu {len(df)})")
    vc = df["cropid"].astype(str).value_counts().head(8)
    print("  mazao yanayojitokeza zaidi (msimbo: idadi):", {k: int(v) for k, v in vc.items()})
    for code in list(vc.index[:3]):
        d = df[df["cropid"].astype(str) == code]
        qty, area = num(d[q]), num(d[a])
        ok = (qty > 0) & (area > 0)
        print(f"  --- zao {code}: safu={len(d)}, kiasi>0 na eneo>0={int(ok.sum())}")
        print(f"      mazao mchanganyiko ({ic}):", {k: int(v) for k, v in d[ic].astype(str).value_counts().items()})
        if ok.sum():
            y = (qty[ok] / (area[ok] * 0.404686)) / 1000        # TUKIFIKIRIA kiasi = kg, eneo = ekari
            print("      mavuno ya kadirio t/ha (kilo dhana) asilimia 5/25/50/75/95:",
                  [round(float(x), 2) for x in y.quantile([.05, .25, .5, .75, .95])])

hh = load("HH_SEC_A")
if hh is not None:
    print("\n===== HH_SEC_A")
    for c in ["int_month_code"]:
        print(f"  {c}:", {str(k): int(v) for k, v in hh[c].value_counts().sort_index().items()})
    print("  Int_End (kwanza..mwisho):", str(hh["Int_End"].min()), "..", str(hh["Int_End"].max()))
    print("  mikoa (t0_region: kaya):", {str(k): int(v) for k, v in hh["t0_region"].value_counts().sort_index().items()})
