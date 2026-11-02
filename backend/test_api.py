from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_route_comparison():
    body = {"routes": [
      {"name":"A","transfers":1,"total_duration_min":30,"total_fare_hkd":15,
       "segments":[{"mode":"bus","operator":"KMB","route_or_line":"91","board":"A","alight":"B","fare_hkd":15,"duration_min":30}]},
      {"name":"B","transfers":0,"total_duration_min":45,"total_fare_hkd":10,
       "segments":[{"mode":"bus","operator":"Citybus","route_or_line":"1","board":"A","alight":"C","fare_hkd":10,"duration_min":45}]}
    ]}
    r = client.post("/tools/compare_routes", json=body)
    assert r.status_code == 200
    assert r.json()["fastest"]["name"] == "A"
    assert r.json()["cheapest"]["name"] == "B"
    assert r.json()["fewest_transfers"]["name"] == "B"
