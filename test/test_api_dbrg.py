import os
from dotenv import load_dotenv
from pathlib import Path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import DbrgClient

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

key = os.getenv("DBRG_API_KEY")
dbrg_client = DbrgClient(key=key)


def test_geocode_format():
    response = dbrg_client.geocode("北京市朝阳区阜通东大街6号")
    assert isinstance(response, dict)
    assert "status" in response
    assert "count" in response
    assert "geocodes" in response
    assert isinstance(response["geocodes"], list)
    for g in response["geocodes"]:
        assert "formatted_address" in g
        assert "location" in g
        loc = g["location"]
        if loc is not None:
            assert "lng" in loc
            assert "lat" in loc


def test_reverse_geocode_format():
    response = dbrg_client.reverse_geocode("116.603034,39.431568")
    assert isinstance(response, dict)
    assert "status" in response
    assert "formatted_address" in response
    assert "location" in response
    loc = response["location"]
    if loc is not None:
        assert "lng" in loc
        assert "lat" in loc


def test_route_planning_driving_format():
    response = dbrg_client.route_planning("116.481028,39.989643", "116.434446,39.90816", mode="driving")
    assert isinstance(response, dict)
    assert "status" in response
    assert "count" in response
    assert "paths" in response
    assert isinstance(response["paths"], list)
    for p in response["paths"]:
        assert "instruction" in p
        assert isinstance(p["instruction"], list)
        assert "polyline" in p
        assert isinstance(p["polyline"], list)
        for pt in p["polyline"]:
            assert "lng" in pt
            assert "lat" in pt


def test_route_planning_walking_format():
    response = dbrg_client.route_planning("116.373509,39.92247", "116.375946,39.919215", mode="walking")
    assert isinstance(response, dict)
    assert "status" in response
    assert "count" in response
    assert "paths" in response
    assert isinstance(response["paths"], list)
    for p in response["paths"]:
        assert "instruction" in p
        assert isinstance(p["instruction"], list)
        assert "polyline" in p
        assert isinstance(p["polyline"], list)
        for pt in p["polyline"]:
            assert "lng" in pt
            assert "lat" in pt


def test_route_planning_bicycling_format():
    response = dbrg_client.route_planning("116.434307,39.90909", "116.434446,39.90816", mode="bicycling")
    assert isinstance(response, dict)
    assert "status" in response
    assert "count" in response
    assert "paths" in response
    assert isinstance(response["paths"], list)
    for p in response["paths"]:
        assert "instruction" in p
        assert isinstance(p["instruction"], list)
        assert "polyline" in p
        assert isinstance(p["polyline"], list)
        for pt in p["polyline"]:
            assert "lng" in pt
            assert "lat" in pt
