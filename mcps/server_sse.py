import os
import json
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from api import direction_distance as calc_distance
from api import AmapClient as Client

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

key = os.getenv("AMAP_API_KEY")
if not key:
    raise RuntimeError("AMAP_API_KEY not found in environment or .env file")

client = Client(key=key)

mcp = FastMCP(
    "gis-web",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


@mcp.tool()
def geocode(address: str, city: str = None) -> str:
    result = client.geocode(address, city)
    return json.dumps({
        "type": "points",
        "isFinal": False,
        "data": result.get("geocodes", []),
    }, ensure_ascii=False)


@mcp.tool()
def geodecode(location: str) -> str:
    result = client.reverse_geocode(location)
    return json.dumps({
        "type": "points",
        "isFinal": False,
        "data": [{
            "location": result.get("location"),
            "address": result.get("formatted_address", ""),
        }],
    }, ensure_ascii=False)


@mcp.tool()
def route_planning(origin: str, destination: str,
                   origin_formatted_address: str = "",
                   destination_formatted_address: str = "",
                   mode: str = "driving", strategy: int = 0) -> str:
    result = client.route_planing(origin, destination, mode, strategy)
    paths = result.get("paths", [])

    lng1, lat1 = map(float, origin.split(","))
    lng2, lat2 = map(float, destination.split(","))

    return json.dumps({
        "type": "polyline",
        "isFinal": False,
        "data": [
            {
                "origin": {"lng": lng1, "lat": lat1, "address": origin_formatted_address},
                "destination": {"lng": lng2, "lat": lat2, "address": destination_formatted_address},
            },
            *paths,
        ],
    }, ensure_ascii=False)


@mcp.tool()
def direction_distance(loc1: str, loc2: str, origin_formatted_address: str = "", destination_formatted_address: str = "") -> str:
    dist = calc_distance(loc1, loc2)
    lng1, lat1 = map(float, loc1.split(","))
    lng2, lat2 = map(float, loc2.split(","))
    return json.dumps({
        "type": "distance",
        "isFinal": False,
        "data": [{
            "origin": {"lng": lng1, "lat": lat1, "address": origin_formatted_address},
            "destination": {"lng": lng2, "lat": lat2, "address": destination_formatted_address},
            "distance": dist,
        }],
    }, ensure_ascii=False)


if __name__ == "__main__":
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8001"))
    app = mcp.sse_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    uvicorn.run(app, host=host, port=port)
