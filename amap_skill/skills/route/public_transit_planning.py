from typing import Optional, Dict, Any
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class PublicTransitPlanningSkill(BaseSkill):
    name = "public_transit_planning"
    description = "公交路径规划，支持公交、地铁等公共交通出行方案查询"
    parameters = [
        {
            "name": "origin",
            "type": "string",
            "description": "起点坐标，格式：经度,纬度",
            "required": True
        },
        {
            "name": "destination",
            "type": "string",
            "description": "终点坐标，格式：经度,纬度",
            "required": True
        },
        {
            "name": "city",
            "type": "string",
            "description": "城市名或adcode，例如北京或010",
            "required": True
        },
        {
            "name": "cityd",
            "type": "string",
            "description": "终点城市名或adcode（跨城时使用），可选",
            "required": False
        },
        {
            "name": "strategy",
            "type": "integer",
            "description": "公交策略：0-最快捷，1-最经济，2-最少换乘，3-最少步行，5-不乘地铁",
            "required": False
        },
        {
            "name": "nightflag",
            "type": "integer",
            "description": "是否计算夜班车：0-不计算，1-计算",
            "required": False
        }
    ]

    async def execute(
        self,
        origin: str,
        destination: str,
        city: str,
        cityd: Optional[str] = None,
        strategy: int = 0,
        nightflag: int = 0
    ) -> str:
        if strategy not in {0, 1, 2, 3, 5}:
            raise ValueError("strategy 必须为 0(最快捷)、1(最经济)、2(最少换乘)、3(最少步行)、5(不乘地铁)")

        params: Dict[str, Any] = {
            "origin": origin,
            "destination": destination,
            "city": city,
            "strategy": strategy,
            "nightflag": nightflag,
            "output": "JSON"
        }

        if cityd:
            params["cityd"] = cityd

        data = await amap_get("/v3/direction/transit/integrated", params)
        route = data.get("route", {})
        transits = route.get("transits", [])

        if not transits:
            return json.dumps({
                "status": "not_found",
                "mode": "public_transit",
                "origin": origin,
                "destination": destination,
                "message": "未找到合适的公交路线"
            }, ensure_ascii=False, indent=2)

        # 取前3条推荐路线
        simplified_transits = []
        for transit in transits[:3]:
            segments = []
            for segment in transit.get("segments", []):
                bus_info = segment.get("bus", {})
                walking_info = segment.get("walking", {})

                seg_out: Dict[str, Any] = {}

                if bus_info and bus_info.get("buslines"):
                    busline = bus_info["buslines"][0]
                    seg_out["type"] = "bus"
                    seg_out["name"] = busline.get("name")
                    seg_out["departure_stop"] = busline.get("departure_stop", {}).get("name")
                    seg_out["arrival_stop"] = busline.get("arrival_stop", {}).get("name")
                    seg_out["via_num"] = busline.get("via_num")
                    seg_out["duration_s"] = busline.get("duration")

                if walking_info:
                    seg_out["type"] = "walking"
                    seg_out["distance_m"] = walking_info.get("distance")
                    seg_out["duration_s"] = walking_info.get("duration")

                segments.append(seg_out)

            simplified_transits.append({
                "duration_s": transit.get("duration"),
                "distance_m": transit.get("distance"),
                "walking_distance_m": transit.get("walking_distance"),
                "cost_cent": transit.get("cost"),
                "segments": segments
            })

        result = {
            "status": "success",
            "mode": "public_transit",
            "origin": origin,
            "destination": destination,
            "city": city,
            "strategy": strategy,
            "routes": simplified_transits
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
