from pathlib import Path
import pandas as pd

root = Path("data/raw/nbs/nps2019")

target_vars = {
    "ag4a_01",
    "ag4a_02",
    "ag4a_04",
    "ag4a_06",
    "ag4a_08",
    "ag4a_10_1",
}

print("\n========== NBS VARIABLE LABEL AUDIT ==========")

for path in sorted(root.rglob("AG_SEC*.dta")):
    try:
        reader = pd.io.stata.StataReader(str(path))

        labels = reader.variable_labels()

        matches = {
            name: label
            for name, label in labels.items()
            if name.lower() in target_vars
        }

        if matches:
            print(f"\nFILE: {path.name}")

            for variable, label in matches.items():
                print(f"{variable}: {label}")

        reader.close()

    except Exception as exc:
        print(f"ERROR: {path.name}: {exc}")

print("\n========== AUDIT COMPLETED ==========")
