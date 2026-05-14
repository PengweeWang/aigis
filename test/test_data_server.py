import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from server.app import app, current

client = TestClient(app)


def test(name, fn):
    try:
        fn()
        print(f"  PASS  {name}")
    except Exception as e:
        print(f"  FAIL  {name}: {e}")


def run():
    # ---------- TestSet ----------

    def test_set_points_without_isFinal():
        r = client.post("/api/set", json={
            "type": "points",
            "data": [{"location": "116.4,39.9", "formatted_address": "北京"}]
        })
        assert r.status_code == 200
        assert r.json() == {"ok": True}

        data = client.get("/api/data").json()
        assert data["isFinal"] is False
        assert data["type"] == "points"
        assert data["data"] == [{"location": "116.4,39.9", "formatted_address": "北京"}]

    test(__name__ + ".TestSet.test_set_points_without_isFinal", test_set_points_without_isFinal)

    def test_set_polyline_with_isFinal():
        r = client.post("/api/set", json={
            "type": "polyline",
            "isFinal": True,
            "data": [[116.39, 39.90], [116.40, 39.91]]
        })
        assert r.status_code == 200

        data = client.get("/api/data").json()
        assert data["isFinal"] is True
        assert data["type"] == "polyline"
        assert data["data"] == [[116.39, 39.90], [116.40, 39.91]]

    test(__name__ + ".TestSet.test_set_polyline_with_isFinal", test_set_polyline_with_isFinal)

    def test_set_overwrites_previous():
        client.post("/api/set", json={
            "type": "points",
            "data": [{"location": "1,1"}]
        })
        client.post("/api/set", json={
            "type": "polyline",
            "data": [[2, 2]]
        })
        data = client.get("/api/data").json()
        assert data["type"] == "polyline"
        assert data["data"] == [[2, 2]]

    test(__name__ + ".TestSet.test_set_overwrites_previous", test_set_overwrites_previous)

    # ---------- TestFinal ----------

    def test_patch_final():
        client.post("/api/set", json={
            "type": "points",
            "data": [{"location": "1,1"}]
        })
        r = client.patch("/api/final", json={"isFinal": True})
        assert r.status_code == 200
        assert r.json() == {"ok": True}

        data = client.get("/api/data").json()
        assert data["isFinal"] is True

    test(__name__ + ".TestFinal.test_patch_final", test_patch_final)

    def test_patch_final_when_no_data():
        current.clear()
        r = client.patch("/api/final", json={"isFinal": True})
        assert r.status_code == 400

    test(__name__ + ".TestFinal.test_patch_final_when_no_data", test_patch_final_when_no_data)

    # ---------- TestGetData ----------

    def test_get_data_empty():
        current.clear()
        assert client.get("/api/data").json() == {}

    test(__name__ + ".TestGetData.test_get_data_empty", test_get_data_empty)

    def test_get_data_after_set():
        client.post("/api/set", json={
            "type": "points",
            "data": [{"location": "1,1"}]
        })
        data = client.get("/api/data").json()
        assert "type" in data
        assert "data" in data
        assert "isFinal" in data

    test(__name__ + ".TestGetData.test_get_data_after_set", test_get_data_after_set)


if __name__ == "__main__":
    run()
