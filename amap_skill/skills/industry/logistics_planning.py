from typing import Optional, Dict, Any, List
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class LogisticsPlanningSkill(BaseSkill):
    name = "logistics_planning"
    description = "物流配送路径规划，支持多途径点、自动优化途径点顺序，适用于快递配送、货运调度等场景"
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
            "name": "waypoints",
            "type": "array",
            "description": "途经点坐标列表，每个元素格式：经度,纬度，最多16个途径点",
            "required": False
        },
        {
            "name": "optimize_order",
            "type": "boolean",
            "description": "是否自动优化途径点顺序，默认true",
            "required": False
        },
        {
            "name": "strategy",
            "type": "integer",
            "description": "驾车策略：0-速度优先，1-费用优先，2-距离优先，10-返回多条路线",
            "required": False
        }
    ]

    async def execute(
        self,
        origin: str,
        destination: str,
        waypoints: Optional[List[str]] = None,
        optimize_order: bool = True,
        strategy: int = 0
    ) -> str:
        params: Dict[str, Any] = {
            "origin": origin,
            "destination": destination,
            "strategy": strategy,
            "extensions": "all",
            "output": "JSON"
        }

        if waypoints:
            if len(waypoints) > 16:
                raise ValueError("途径点最多16个，请分批规划")
            params["waypoints"] = ";".join(waypoints)
            if optimize_order:
                params["waypoints"] += "||optimize"

        data = await amap_get("/v3/direction/driving", params)
        route = data.get("route", {})
        paths = route.get("paths", [])

        if not paths:
            return json.dumps({
                "status": "not_found",
                "mode": "logistics",
                "origin": origin,
                "destination": destination,
                "waypoints": waypoints or [],
                "message": "未找到合适的物流路线"
            }, ensure_ascii=False, indent=2)

        simplified_paths = []
        for path in paths[:3]:
            steps = []
            for step in path.get("steps", [])[:60]:
                steps.append({
                    "instruction": step.get("instruction"),
                    "road": step.get("road"),
                    "distance_m": step.get("distance"),
                    "duration_s": step.get("duration"),
                    "action": step.get("action"),
                    "tolls": step.get("tolls")
                })

            simplified_paths.append({
                "distance_m": path.get("distance"),
                "duration_s": path.get("duration"),
                "tolls": path.get("tolls"),
                "steps": steps
            })

        result = {
            "status": "success",
            "mode": "logistics",
            "origin": origin,
            "destination": destination,
            "waypoints": waypoints or [],
            "optimize_order": optimize_order,
            "taxi_cost": route.get("taxi_cost"),
            "routes": simplified_paths
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
