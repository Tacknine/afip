import json
from pathlib import Path
import joblib

root = Path(__file__).resolve().parents[1]
folder = root / "artifacts" / "seed_quantity"

with open(folder / "metadata.json", encoding="utf-8") as f:
    m = json.load(f)

print("=" * 80)
print("SAVED MODEL METADATA")
print("=" * 80)
print(json.dumps(m, indent=4, ensure_ascii=False, default=str))

print("\n" + "=" * 80)
print("SAVED MODEL STRUCTURE")
print("=" * 80)

model = joblib.load(folder / "model.joblib")

print("Class:", type(model))
print("Module:", type(model).__module__)
print("Has predict:", hasattr(model, "predict"))
print("Features:", getattr(model, "feature_names_in_", None))
print("Feature count:", getattr(model, "n_features_in_", None))

if hasattr(model, "named_steps"):
    print("\nPipeline steps:")
    for name, step in model.named_steps.items():
        print(name, "=>", type(step))

