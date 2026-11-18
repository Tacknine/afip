from pathlib import Path
import pyreadstat

BASE = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

FILES = [
    "AG_SEC_4A.dta",
    "AG_SEC_4B.dta",
]

KEYWORDS = [
    "seed", "fertilizer", "fertiliser", "manure",
    "irrigation", "rain", "water", "soil",
    "plant", "harvest", "land", "area",
    "labor", "labour", "pesticide", "chemical",
    "variety", "crop", "month", "season",
    "tractor", "equipment", "organic",
]

print("=" * 100)
print("AFIP - AGRICULTURAL FEATURE DISCOVERY")
print("=" * 100)

for filename in FILES:
    path = BASE / filename

    print("\n" + "=" * 100)
    print("FILE:", filename)
    print("=" * 100)

    if not path.exists():
        print("FILE NOT FOUND:", path)
        continue

    _, meta = pyreadstat.read_dta(
        str(path),
        metadataonly=True
    )

    names = meta.column_names
    labels = meta.column_labels

    print("TOTAL VARIABLES:", len(names))
    print("\nRELEVANT VARIABLE CANDIDATES:\n")

    found = 0

    for name, label in zip(names, labels):
        label = label or ""
        search_text = f"{name} {label}".lower()

        if any(word in search_text for word in KEYWORDS):
            print(f"{name:25} | {label}")
            found += 1

    print("\nCANDIDATES FOUND:", found)

print("\nFEATURE DISCOVERY COMPLETED.")
print("RAW DATA WAS NOT MODIFIED.")
print("MODEL TRAINING WAS NOT STARTED.")
