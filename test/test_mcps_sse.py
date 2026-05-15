import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcps.server_sse import (
    geocode,
    geodecode,
    route_planning,
    direction_distence,
)


def check_envelope(obj, expected_type):
    assert isinstance(obj, dict), "result must be a dict"
    assert obj.get("type") == expected_type, f"type should be '{expected_type}', got {obj.get('type')}"
    assert obj.get("isFinal") is False, "isFinal must be false"
    assert "data" in obj, "data field is required"
    assert isinstance(obj["data"], list), "data must be a list"
    return obj["data"]


def test_geocode():
    raw = geocode("北京市朝阳区阜通东大街6号")
    obj = json.loads(raw)
    data = check_envelope(obj, "points")

    assert len(data) > 0, "geocode should return at least one result"
    for item in data:
        assert "formatted_address" in item
        assert "location" in item
        loc = item["location"]
        assert isinstance(loc, dict)
        assert "lng" in loc and "lat" in loc

    print("=== geocode ===")
    print(json.dumps(obj, indent=2, ensure_ascii=False))
    print()


def test_geodecode():
    raw = geodecode("116.482145,39.990039")
    obj = json.loads(raw)
    data = check_envelope(obj, "points")

    assert len(data) == 1
    item = data[0]
    assert "location" in item
    assert "address" in item
    loc = item["location"]
    assert isinstance(loc, dict)
    assert "lng" in loc and "lat" in loc

    print("=== geodecode ===")
    print(json.dumps(obj, indent=2, ensure_ascii=False))
    print()


def test_route_planning():
    raw = route_planning(
        "116.434327,39.909045",
        "116.434818,39.908655",
        origin_formatted_address="北京市东城区建国门",
        destination_formatted_address="北京市东城区朝阳门",
        mode="bicycling",
    )
    obj = json.loads(raw)
    data = check_envelope(obj, "polyline")

    assert len(data) >= 2, "polyline data should have origin/destination header + at least one path"
    header = data[0]
    assert "origin" in header
    assert "destination" in header

    for path in data[1:]:
        assert "instruction" in path
        assert "polyline" in path
        for pt in path["polyline"]:
            assert "lng" in pt and "lat" in pt

    print("=== route_planning ===")
    print(json.dumps(obj, indent=2, ensure_ascii=False))
    print()


def test_direction_distence():
    raw = direction_distence(
        "116.397428,39.90923",
        "116.417428,39.92923",
        origin_formatted_address="北京市东城区东直门",
        destination_formatted_address="北京市东城区雍和宫",
    )
    obj = json.loads(raw)
    data = check_envelope(obj, "distence")

    assert len(data) == 1
    item = data[0]
    assert "origin" in item
    assert "destination" in item
    assert "distence" in item
    assert isinstance(item["distence"], (int, float))
    assert item["distence"] > 0

    print("=== direction_distence ===")
    print(json.dumps(obj, indent=2, ensure_ascii=False))
    print()


if __name__ == "__main__":
    test_geocode()
    test_geodecode()
    test_route_planning()
    test_direction_distence()
