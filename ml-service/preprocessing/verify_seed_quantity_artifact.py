from pathlib import Path
import json
import joblib

ROOT = Path(__file__).resolve().parents[1]

ARTIFACT_DIR = ROOT / "artifacts" / "seed_quantity"
MODEL_PATH = ARTIFACT_DIR / "model.joblib"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"
TRAINING_FILE = ROOT / "train_all_models.py"

def section(title):
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)

section("AFIP SEED QUANTITY - ARTIFACT VERIFICATION")

# ============================================================
# 1. VERIFY FILES
# ============================================================

section("1. ARTIFACT FILE VERIFICATION")

for path in [MODEL_PATH, METADATA_PATH]:
    print(f"\nFile: {path}")
    print(f"Exists: {path.exists()}")

    if path.exists():
        print(f"Size: {path.stat().st_size:,} bytes")

if not MODEL_PATH.exists():
    raise FileNotFoundError(MODEL_PATH)

if not METADATA_PATH.exists():
    raise FileNotFoundError(METADATA_PATH)

# ============================================================
# 2. READ METADATA
# ============================================================

section("2. SAVED MODEL METADATA")

with open(METADATA_PATH, "r", encoding="utf-8") as file:
    metadata = json.load(file)

print(json.dumps(metadata, indent=4, ensure_ascii=False))

# ============================================================
# 3. LOAD MODEL OBJECT
# ============================================================

section("3. SAVED MODEL OBJECT")

model = joblib.load(MODEL_PATH)

print("Python class:", type(model))
print("Class module:", type(model).__module__)

print("\nHas predict():", hasattr(model, "predict"))
print("Has named_steps:", hasattr(model, "named_steps"))
print("Has feature_names_in_:", hasattr(model, "feature_names_in_"))
print("Has n_features_in_:", hasattr(model, "n_features_in_"))

if hasattr(model, "feature_names_in_"):
    print("\nFEATURE NAMES:")
    for feature in model.feature_names_in_:
        print("-", feature)

if hasattr(model, "n_features_in_"):
    print("\nNUMBER OF INPUT FEATURES:")
    print(model.n_features_in_)

# ============================================================
# 4. INSPECT PIPELINE
# ============================================================

section("4. MODEL PIPELINE")

if hasattr(model, "named_steps"):
    for name, step in model.named_steps.items():
        print(f"\nSTEP: {name}")
        print("CLASS:", type(step))

        if hasattr(step, "transformers_"):
            print("TRANSFORMERS:")
            for transformer in step.transformers_:
                print(transformer)

        if hasattr(step, "feature_importances_"):
            print("FEATURE IMPORTANCES:")
            print(step.feature_importances_)

        if hasattr(step, "n_estimators"):
            print("N_ESTIMATORS:", step.n_estimators)

        if hasattr(step, "max_depth"):
            print("MAX_DEPTH:", step.max_depth)
else:
    print("Saved object is not a named sklearn Pipeline.")

# ============================================================
# 5. TRAINING CODE REVIEW
# ============================================================

section("5. TRAINING AND VALIDATION CODE")

if TRAINING_FILE.exists():
    lines = TRAINING_FILE.read_text(
        encoding="utf-8-sig"
    ).splitlines()

    start_line = 285
    end_line = 505

    for index in range(start_line - 1, min(end_line, len(lines))):
        print(f"{index + 1:04}: {lines[index]}")
else:
    print("Training file not found.")

# ============================================================
# 6. IMPORTANT METADATA CHECKS
# ============================================================

section("6. PROVENANCE CHECKS")

checks = {
    "model_name": metadata.get("model_name"),
    "status": metadata.get("status"),
    "validation_status": metadata.get("validation_status"),
    "version": metadata.get("version"),
    "trained_at": metadata.get("trained_at"),
    "training_rows": metadata.get("training_rows"),
    "testing_rows": metadata.get("testing_rows"),
    "split_method": metadata.get("split_method"),
    "metrics": metadata.get("metrics"),
    "data_audit": metadata.get("data_audit")
}

for key, value in checks.items():
    print(f"\n{key}:")
    print(json.dumps(value, indent=4, ensure_ascii=False, default=str))

section("VERIFICATION COMPLETED")

print("RAW DATA MODIFIED: NO")
print("MODEL RETRAINED: NO")
print("MODEL FILE MODIFIED: NO")
print("PREDICTIONS GENERATED: NO")
print("AUDIT COMPLETED: YES")
