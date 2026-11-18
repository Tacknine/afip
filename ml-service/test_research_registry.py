from model_registry import (
    list_models,
    get_model,
    get_research_models,
    get_production_models
)

registry = list_models()

print("=" * 70)
print("AFIP RESEARCH MODEL REGISTRY TEST")
print("=" * 70)

candidate = registry["research_models"][
    "seed_quantity_crop_median"
]

print("\nTEST 1: Candidate registration")
print(candidate)

assert candidate["available"] is True
assert candidate["status"] == "research_only"

print("\nTEST 2: Production protection")

assert candidate["production_approved"] is False
assert candidate["production_ready"] is False

print("PASS: Candidate is not production approved.")

print("\nTEST 3: Research model retrieval")

research = get_research_models()

assert "seed_quantity_crop_median" in research

print("PASS: Research model retrieved.")

print("\nTEST 4: Direct model retrieval")

model = get_model("seed_quantity_crop_median")

assert model["research_only"] is True

print("PASS: Direct retrieval works.")

print("\nTEST 5: Production isolation")

production = get_production_models()

assert "seed_quantity_crop_median" not in production

print("PASS: Research candidate excluded from production.")

print("\nTEST 6: Existing model registration")

for name in [
    "seed_quantity",
    "maize_yield",
    "crop_recommendation",
    "crop_production"
]:
    assert name in registry["models"]

print("PASS: Existing registry entries preserved.")

print("\nALL REGISTRY TESTS COMPLETED.")
