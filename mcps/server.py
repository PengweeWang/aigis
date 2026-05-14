import os
import json
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from api import AmapClient, direction_distence as calc_distance

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

key = os.getenv("AMAP_API_KEY")
if not key:
    raise RuntimeError("AMAP_API_KEY not found in environment or .env file")

DATA_SERVER = os.getenv("DATA_SERVER_URL", "http://localhost:8000")

client = AmapClient(key=key)

mcp = FastMCP("gis")

# ---------------------------------------------------------------------------
# helper – push data into the fastapi storage (without isFinal)
# ---------------------------------------------------------------------------
def _set(typ: str, data: list) -> None:
    try:
        import requests
        requests.post(
            f"{DATA_SERVER}/api/set",
            json={"type": typ, "data": data},
            timeout=5,
        )
    except Exception:
        pass


def _patch_final(isFinal: bool) -> None:
    try:
        import requests
        requests.patch(
            f"{DATA_SERVER}/api/final",
            json={"isFinal": isFinal},
            timeout=5,
        )
    except Exception:
        pass


@mcp.tool()
def set_final(isFinal: bool) -> str:
    """
    Mark the currently stored data as final or not.
    :param isFinal: Whether the data is the final data.
    :return: A confirmation message.
    """
    _patch_final(isFinal)
    return json.dumps({"ok": True, "isFinal": isFinal}, ensure_ascii=False)


@mcp.tool()
def geocode(address: str, city: str = None) -> str:
    """
    Get geocode information for a given address.
    :param address: The address to geocode.
    :param city: Optional city parameter to narrow down the search.
    :return: A JSON string containing geocode information.
    The raw coordinates are pushed to the data server for the frontend.
    """
    result = client.geocode(address, city)
    geos = result.get("geocodes", [])
    _set("points", geos)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def geodecode(location: str) -> str:
    """
    Get address information for a given geocode location.
    :param location: The geocode location in the format "longitude,latitude".
    :return: A JSON string containing address information.
    """
    result = client.reverse_geocode(location)
    _set("points", [{"location": result.get("location"), "address": result.get("formatted_address", "")}])
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def route_planning(origin: str, destination: str, 
                   origin_formatted_address: str = "", 
                   destination_formatted_address: str = "", 
                   mode: str = "driving", strategy: int = 0) -> str:
    """
    Get route planning information between an origin and a destination.
    :param origin: The starting point in the format "longitude,latitude".
    :param destination: The ending point in the format "longitude,latitude".
    :param origin_formatted_address: The formatted address of the origin point.
    :param destination_formatted_address: The formatted address of the destination point.
    :param mode: The mode of transportation, can be "driving", "walking", or "bicycling".
    :param strategy: The strategy for route planning, only applicable for driving mode. 
                     0: Recommended route (default)， It is not recommended to choose 
                     any other mode.
    :return: A JSON string containing route planning information.
    Polyline coordinates are pushed to the data server for the frontend.
    ```
    """
    result = client.route_planing(origin, destination, mode, strategy)
    paths = result.get("paths", [])

    lng1, lat1 = map(float, origin.split(","))
    lng2, lat2 = map(float, destination.split(","))

    _set("polyline", [
        {
            "origin": {"lng": lng1, "lat": lat1, "address": origin_formatted_address},
            "destination": {"lng": lng2, "lat": lat2, "address": destination_formatted_address},
        },
        *paths,
    ])

    for p in paths:
        p.pop("polyline", None)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def direction_distence(loc1: str, loc2: str, origin_formatted_address: str = "", destination_formatted_address: str = "") -> float:
    """
    Calculate the distance between two locations.
    :param loc1: The first location in the format "longitude,latitude".
    :param loc2: The second location in the format "longitude,latitude".
    :param origin_formatted_address: The formatted address of the first location.
    :param destination_formatted_address: The formatted address of the second location.
    :return: The distance between the two locations in meters.
    """
    dist = calc_distance(loc1, loc2)
    lng1, lat1 = map(float, loc1.split(","))
    lng2, lat2 = map(float, loc2.split(","))
    _set("distence", [{
        "origin": {"lng": lng1, "lat": lat1, "address": origin_formatted_address},
        "destination": {"lng": lng2, "lat": lat2, "address": destination_formatted_address},
        "distence": dist,
    }])
    return dist


if __name__ == "__main__":
    mcp.run()
