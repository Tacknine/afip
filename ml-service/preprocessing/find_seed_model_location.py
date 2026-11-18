from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

print("=" * 100)
print("AFIP - SAVED MODEL LOCATION INVESTIGATION")
print("=" * 100)

EXCLUDED = {
    ".venv",
    "__pycache__",
    ".git",
    "node_modules",
    "audit_results"
}

MODEL_EXTENSIONS = {
    ".pkl", ".joblib", ".sav", ".model", ".pickle", ".onnx"
}

print("\n1. MODEL FILES FOUND IN PROJECT")

found = []

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue

    if any(part in EXCLUDED for part in path.parts):
        continue

    if path.suffix.lower() in MODEL_EXTENSIONS:
        found.append(path)

if found:
    for path in found:
        print(f"\nFILE: {path.name}")
        print(f"PATH: {path}")
        print(f"SIZE: {path.stat().st_size:,} bytes")
else:
    print("NO MODEL FILES FOUND.")

print("\n" + "=" * 100)
print("2. FILES WITH MODEL-RELATED NAMES")
print("=" * 100)

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue

    if any(part in EXCLUDED for part in path.parts):
        continue

    name = path.name.lower()

    if any(word in name for word in [
        "seed", "metadata", "artifact", "model", "train"
    ]):
        print(path.relative_to(ROOT))

print("\n" + "=" * 100)
print("3. MODEL SAVING CODE IN train_all_models.py")
print("=" * 100)

training_file = ROOT / "train_all_models.py"

if training_file.exists():
    lines = training_file.read_text(
        encoding="utf-8-sig"
    ).splitlines()

    keywords = [
        "joblib.dump",
        "pickle.dump",
        "model.save",
        "save_model",
        "model_path",
        "artifact",
        "metadata",
        "seed_quantity"
    ]

    matching = [
        i for i, line in enumerate(lines)
        if any(keyword in line.lower() for keyword in keywords)
    ]

    displayed = set()

    for index in matching:
        start = max(0, index - 3)
        end = min(len(lines), index + 5)

        for i in range(start, end):
            if i not in displayed:
                print(f"{i + 1:04}: {lines[i]}")
                displayed.add(i)

        print("-" * 70)
else:
    print("train_all_models.py NOT FOUND.")

print("\n" + "=" * 100)
print("INVESTIGATION COMPLETED")
print("NO FILES MODIFIED")
print("NO MODEL TRAINED")
print("=" * 100)
