from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP


AMAP_BASE_URL = "https://restapi.amap.com"
ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_SEARCH_PATHS: List[Path] = []


def _iter_env_candidates() -> List[Path]:
    candidates: List[Path] = []

    explicit = os.getenv("AMAP_DOTENV_PATH")
    if explicit:
        candidates.append(Path(explicit))

    cwd = Path.cwd().resolve()
    module_dir = Path(__file__).resolve().parent

    candidates.append(cwd / ".env")
    candidates.append(ROOT_DIR / ".env")

    for parent in cwd.parents:
        candidates.append(parent / ".env")
        if (parent / "opencode.json").is_file():
            candidates.append(parent / ".env")

    for parent in module_dir.parents:
        candidates.append(parent / ".env")
        if (parent / "opencode.json").is_file():
            candidates.append(parent / ".env")

    return candidates


def _load_env_file() -> None:
    """Load key-value pairs from .env into os.environ if missing."""
    candidates = _iter_env_candidates()
    visited = set()
    searched: List[Path] = []

    for env_path in candidates:
        resolved = env_path.resolve()
        if resolved in visited:
            continue
        visited.add(resolved)
        searched.append(resolved)
        if not env_path.is_file():
            continue

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and not os.getenv(key):
                os.environ[key] = value

    ENV_SEARCH_PATHS.clear()
    ENV_SEARCH_PATHS.extend(searched)


_load_env_file()


class AMapAPIError(RuntimeError):
    """Raised when AMap API returns an error response."""


def get_amap_key() -> str:
    key = os.getenv("AMAP_API_KEY")
    if not key:
        searched = ", ".join(str(p) for p in ENV_SEARCH_PATHS[:6])
        if len(ENV_SEARCH_PATHS) > 6:
            searched = f"{searched}, ..."
        raise AMapAPIError(
            "Environment variable AMAP_API_KEY is not set (and no AMAP_API_KEY found in .env). "
            f"Searched: {searched}"
        )
    return key


async def amap_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    query = dict(params)
    query["key"] = get_amap_key()

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"{AMAP_BASE_URL}{path}", params=query)
        response.raise_for_status()
        data = response.json()

    status = str(data.get("status", ""))
    if status != "1":
        info = data.get("info", "Unknown error")
        infocode = data.get("infocode", "")
        raise AMapAPIError(f"AMap API error: {info} (infocode={infocode})")
    return data


def _compact_walk_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for step in steps:
        result.append(
            {
                "instruction": step.get("instruction"),
                "road": step.get("road"),
                "distance_m": step.get("distance"),
                "duration_s": step.get("duration"),
                "action": step.get("action"),
                "assistant_action": step.get("assistant_action"),
            }
        )
    return result


def _compact_drive_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for step in steps:
        result.append(
            {
                "instruction": step.get("instruction"),
                "road": step.get("road"),
                "distance_m": step.get("distance"),
                "duration_s": step.get("duration"),
                "tolls": step.get("tolls"),
                "action": step.get("action"),
                "assistant_action": step.get("assistant_action"),
            }
        )
    return result


mcp = FastMCP("amap-gis-mcp")


@mcp.tool()
async def geocode(address: str, city: Optional[str] = None) -> str:
    """
    将结构化地址转换为经纬度坐标。

    参数:
    - address: 结构化地址，例如“北京市朝阳区阜通东大街6号”
    - city: 可选，城市名/拼音/citycode/adcode
    """
    params: Dict[str, Any] = {"address": address, "output": "JSON"}
    if city:
        params["city"] = city

    data = await amap_get("/v3/geocode/geo", params)
    geocodes = data.get("geocodes", [])
    if not geocodes:
        return json.dumps(
            {"query": address, "result": None}, ensure_ascii=False, indent=2
        )

    first = geocodes[0]
    output = {
        "query": address,
        "city": city,
        "result": {
            "formatted": {
                "province": first.get("province"),
                "city": first.get("city"),
                "district": first.get("district"),
                "street": first.get("street"),
                "number": first.get("number"),
            },
            "location": first.get("location"),
            "adcode": first.get("adcode"),
            "level": first.get("level"),
        },
        "candidates": len(geocodes),
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


@mcp.tool()
async def reverse_geocode(
    location: str, radius: int = 1000, extensions: str = "base"
) -> str:
    """
    将经纬度转换为结构化地址。

    参数:
    - location: 经度,纬度，例如“116.481028,39.989643”
    - radius: 搜索半径，0-3000米
    - extensions: base 或 all
    """
    if extensions not in {"base", "all"}:
        raise ValueError("extensions must be 'base' or 'all'")

    params = {
        "location": location,
        "radius": max(0, min(radius, 3000)),
        "extensions": extensions,
        "output": "JSON",
    }
    data = await amap_get("/v3/geocode/regeo", params)
    regeocode = data.get("regeocode", {})
    component = regeocode.get("addressComponent", {})
    out: Dict[str, Any] = {
        "location": location,
        "formatted_address": regeocode.get("formatted_address"),
        "address_component": {
            "country": component.get("country"),
            "province": component.get("province"),
            "city": component.get("city"),
            "district": component.get("district"),
            "township": component.get("township"),
            "adcode": component.get("adcode"),
        },
    }

    if extensions == "all":
        pois = regeocode.get("pois", [])
        roads = regeocode.get("roads", [])
        out["nearby_pois"] = [
            {
                "name": poi.get("name"),
                "type": poi.get("type"),
                "distance_m": poi.get("distance"),
                "location": poi.get("location"),
            }
            for poi in pois[:10]
        ]
        out["nearby_roads"] = [
            {
                "name": road.get("name"),
                "distance_m": road.get("distance"),
                "direction": road.get("direction"),
            }
            for road in roads[:10]
        ]

    return json.dumps(out, ensure_ascii=False, indent=2)


@mcp.tool()
async def route_planning(
    origin: str,
    destination: str,
    mode: str = "driving",
    city: Optional[str] = None,
    strategy: Optional[int] = None,
    extensions: str = "base",
) -> str:
    """
    路径规划（步行/驾车/公交）。

    参数:
    - origin: 起点，经度,纬度
    - destination: 终点，经度,纬度
    - mode: driving | walking | transit
    - city: 公交模式必填，城市名或 citycode
    - strategy: 驾车或公交策略（可选）
    - extensions: base 或 all
    """
    if mode not in {"driving", "walking", "transit"}:
        raise ValueError("mode must be one of: driving, walking, transit")
    if extensions not in {"base", "all"}:
        raise ValueError("extensions must be 'base' or 'all'")

    if mode == "walking":
        data = await amap_get(
            "/v3/direction/walking",
            {
                "origin": origin,
                "destination": destination,
                "output": "JSON",
            },
        )
        paths = data.get("route", {}).get("paths", [])
        if not paths:
            return json.dumps(
                {"mode": mode, "result": None}, ensure_ascii=False, indent=2
            )
        best = paths[0]
        out = {
            "mode": mode,
            "origin": origin,
            "destination": destination,
            "distance_m": best.get("distance"),
            "duration_s": best.get("duration"),
            "steps": _compact_walk_steps(best.get("steps", [])[:30]),
        }
        return json.dumps(out, ensure_ascii=False, indent=2)

    if mode == "driving":
        params: Dict[str, Any] = {
            "origin": origin,
            "destination": destination,
            "extensions": extensions,
            "output": "JSON",
        }
        if strategy is not None:
            params["strategy"] = strategy

        data = await amap_get("/v3/direction/driving", params)
        route = data.get("route", {})
        paths = route.get("paths", [])
        if not paths:
            return json.dumps(
                {"mode": mode, "result": None}, ensure_ascii=False, indent=2
            )
        best = paths[0]
        out = {
            "mode": mode,
            "origin": origin,
            "destination": destination,
            "distance_m": best.get("distance"),
            "duration_s": best.get("duration"),
            "tolls": best.get("tolls"),
            "taxi_cost": route.get("taxi_cost"),
            "strategy": best.get("strategy"),
            "steps": _compact_drive_steps(best.get("steps", [])[:60]),
        }
        return json.dumps(out, ensure_ascii=False, indent=2)

    if not city:
        raise ValueError("city is required when mode='transit'")

    params = {
        "origin": origin,
        "destination": destination,
        "city": city,
        "extensions": extensions,
        "output": "JSON",
    }
    if strategy is not None:
        params["strategy"] = strategy

    data = await amap_get("/v3/direction/transit/integrated", params)
    route = data.get("route", {})
    transits = route.get("transits", [])
    if not transits:
        return json.dumps({"mode": mode, "result": None}, ensure_ascii=False, indent=2)

    best = transits[0]
    segments = best.get("segments", [])
    segment_summary = []
    for seg in segments[:20]:
        buslines = seg.get("bus", {}).get("buslines", [])
        walking = seg.get("walking", {})
        segment_summary.append(
            {
                "walking_distance_m": walking.get("distance"),
                "buslines": [line.get("name") for line in buslines[:3]],
            }
        )

    out = {
        "mode": mode,
        "origin": origin,
        "destination": destination,
        "city": city,
        "distance_m": route.get("distance"),
        "duration_s": best.get("duration"),
        "cost": best.get("cost"),
        "walking_distance_m": best.get("walking_distance"),
        "taxi_cost": route.get("taxi_cost"),
        "segments": segment_summary,
    }
    return json.dumps(out, ensure_ascii=False, indent=2)


@mcp.tool()
async def distance_measure(origin: str, destination: str, mode: str = "driving") -> str:
    """
    距离量算（基于路径规划距离）。

    参数:
    - origin: 起点，经度,纬度
    - destination: 终点，经度,纬度
    - mode: driving | walking
    """
    if mode not in {"driving", "walking"}:
        raise ValueError("mode must be 'driving' or 'walking'")

    planning = json.loads(
        await route_planning(
            origin=origin,
            destination=destination,
            mode=mode,
            extensions="base",
        )
    )

    distance_m = planning.get("distance_m")
    duration_s = planning.get("duration_s")
    out = {
        "mode": mode,
        "origin": origin,
        "destination": destination,
        "distance_m": distance_m,
        "distance_km": round(float(distance_m) / 1000, 3)
        if distance_m is not None
        else None,
        "duration_s": duration_s,
        "duration_min": round(float(duration_s) / 60, 2)
        if duration_s is not None
        else None,
    }
    return json.dumps(out, ensure_ascii=False, indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
