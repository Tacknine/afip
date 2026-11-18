from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

print("=" * 65)
print("AFIP SEED QUANTITY API TEST")
print("=" * 65)

# Test candidate with known crop
response = client.post(
    "/predict/seed-quantity/research/candidate",
    json={"features": {"cropid": 11}}
)

print("\nTEST 1: Known crop")
print("HTTP:", response.status_code)
print(response.json())

# Test unknown crop fallback
response = client.post(
    "/predict/seed-quantity/research/candidate",
    json={"features": {"cropid": 999999}}
)

print("\nTEST 2: Unknown crop")
print("HTTP:", response.status_code)
print(response.json())

# Test missing cropid
response = client.post(
    "/predict/seed-quantity/research/candidate",
    json={"features": {}}
)

print("\nTEST 3: Missing cropid")
print("HTTP:", response.status_code)
print(response.json())

# Verify production endpoint remains protected
response = client.post(
    "/predict/seed-quantity",
    json={
        "features": {
            "cropid": 11,
            "ag4a_01": 1,
            "ag4a_02": 2,
            "ag4a_04": 1,
            "ag4a_06": 1,
            "ag4a_08": 1
        }
    }
)

print("\nTEST 4: Production protection")
print("HTTP:", response.status_code)
print(response.json())

print("\nAPI TESTING COMPLETED.")
