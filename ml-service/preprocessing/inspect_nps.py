"""Kagua faili halisi za NPS 2019/20. Inachapisha MUHTASARI wa takwimu tu (hakuna vitambulisho vya kaya)."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "data" / "raw" / "nbs"
num = lambda s: pd.to_numeric(s, errors="coerce")

def load(name):
    hits = [p for p in ROOT.rglob("*.dta") if p.stem.lower() == name.lower()]
    if not hits:
        print(f"!! {name}.dta haipo")
        return None, None
    try:
        return pd.read_stata(hits[0]), hits[0]
    except Exception:
        return pd.read_stata(hits[0], convert_categoricals=False), hits[0]

def label(path, col):
    try:
        with pd.read_stata(path, iterator=True) as r:
            return r.variable_labels().get(col, "")
    except Exception:
        return ""

def stats(s, name):
    s = num(s)
    print(f"  {name}: zilizopo={int(s.notna().sum())}/{len(s)}  min={s.min()}  mediani={s.median()}  max={s.max()}")

print("\n===== AG_SEC_02 (mashamba)")
ag2, p2 = load("AG_SEC_02")
if ag2 is not None:
    print("  safu:", len(ag2), "| kaya:", ag2["sdd_hhid"].nunique())
    for c in ["ag2a_07__Latitude", "ag2a_07__Longitude", "ag2a_09", "ag2a_04"]:
        stats(ag2[c], c)
    pairs = ag2[["ag2a_07__Latitude", "ag2a_07__Longitude"]].apply(num).dropna().round(4).drop_duplicates()
    print("  viwianishi tofauti (kati ya mashamba yenye GPS):", len(pairs))

for name, p in [("AG_SEC_4A", "ag4a"), ("AG_SEC_4B", "ag4b")]:
    print(f"\n===== {name} (mazao)")
    df, path = load(name)
    if df is None:
        continue
    q = "ag4a_27" if p == "ag4a" else "ag4b_28"
    a = f"{p}_21"
    ic = f"{p}_04"
    print("  safu:", len(df))
    print(f"  lebo {q}: {label(path, q)}")
    print(f"  lebo {a}: {label(path, a)}")
    crops = df["cropid"].astype(str)
    mask = crops.str.lower().str.contains("maize|mahindi", na=False)
    if mask.any():
        print("  jina la zao la mahindi kwenye lebo:", sorted(crops[mask].unique()))
    else:
        print("  hakuna 'maize' kwenye lebo. Mazao ya kwanza 40:", sorted(crops.unique())[:40])
    mz = df[mask]
    print("  safu za mahindi:", len(mz), "| mashamba:", mz[["sdd_hhid", "plotnum"]].drop_duplicates().shape[0])
    if len(mz):
        stats(mz[q], q)
        stats(mz[a], a)
        print(f"  {ic} (mazao mchanganyiko):", {k: int(v) for k, v in mz[ic].astype(str).value_counts().items()})
        ok = (num(mz[q]) > 0) & (num(mz[a]) > 0)
        print("  safu zenye kiasi>0 na eneo>0:", int(ok.sum()))
        if ag2 is not None:
            k = mz.loc[ok, ["sdd_hhid", "plotnum"]].merge(
                ag2[["sdd_hhid", "plotnum", "ag2a_07__Latitude"]], on=["sdd_hhid", "plotnum"], how="left")
            print("  kati ya hizo, zenye GPS ya shamba:", int(num(k["ag2a_07__Latitude"]).notna().sum()))

print("\n===== HH_SEC_A (mahali)")
hh, _ = load("HH_SEC_A")
if hh is not None:
    print("  safu:", len(hh))
    print("  majina ya safu:", list(hh.columns))
    for c in hh.columns:
        if any(k in c.lower() for k in ("region", "district", "ward", "strata", "cluster", "ea_")):
            print(f"  {c}: thamani za kipekee = {hh[c].nunique()}")
