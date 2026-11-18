from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

routes = [
    "/registry",
    "/registry/production",
    "/registry/research"
]

for route in routes:
    response = client.get(route)

    print("\nROUTE:", route)
    print("HTTP:", response.status_code)

    assert response.status_code == 200

    data = response.json()

    if route == "/registry":
        candidate = data["research_models"]["seed_quantity_crop_median"]
        assert candidate["research_only"] is True
        assert candidate["production_approved"] is False

    elif route == "/registry/research":
        assert "seed_quantity_crop_median" in data["models"]

    elif route == "/registry/production":
        assert "seed_quantity_crop_median" not in data["models"]

    print("PASS")

print("\nALL REGISTRY API TESTS PASSED.")
