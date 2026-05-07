from typing import Optional, Dict, Any
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class TruckPlanningSkill(BaseSkill):
    name = "truck_planning"
    description = "货车路径规划，针对货车限行规则规划路线，支持设置车辆参数"
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
            "name": "truck_type",
            "type": "integer",
            "description": "车辆类型：1-微型货车(总质量<1.8吨)，2-轻型货车(1.8-6吨)，3-中型货车(6-14吨)，4-重型货车(>14吨)",
            "required": False
        },
        {
            "name": "weight",
            "type": "number",
            "description": "货车总质量（吨），默认1.5",
            "required": False
        },
        {
            "name": "height",
            "type": "number",
            "description": "货车高度（米），默认3.5",
            "required": False
        },
        {
            "name": "width",
            "type": "number",
            "description": "货车宽度（米），默认2.5",
            "required": False
        },
        {
            "name": "load_weight",
            "type": "number",
            "description": "核定载质量（吨），默认10",
            "required": False
        },
        {
            "name": "axis",
            "type": "integer",
            "description": "轴数，默认2",
            "required": False
        },
        {
            "name": "strategy",
            "type": "integer",
            "description": "路径策略：0-速度最快，1-费用最少，2-距离最短，10-返回多条路线",
            "required": False
        }
    ]

    async def execute(
        self,
        origin: str,
        destination: str,
        truck_type: int = 2,
        weight: float = 1.5,
        height: float = 3.5,
        width: float = 2.5,
        load_weight: float = 10.0,
        axis: int = 2,
        strategy: int = 0
    ) -> str:
        params: Dict[str, Any] = {
            "origin": origin,
            "destination": destination,
            "truck_type": max(1, min(truck_type, 4)),
            "weight": weight,
            "height": height,
            "width": width,
            "load_weight": load_weight,
            "axis": max(2, min(axis, 6)),
            "strategy": strategy,
            "output": "JSON"
        }

        data = await amap_get("/v4/direction/truck", params)
        route = data.get("route", {})
        paths = route.get("paths", [])

        if not paths:
            return json.dumps({
                "status": "not_found",
                "mode": "truck",
                "origin": origin,
                "destination": destination,
                "message": "未找到合适的货车路线，请检查限行区域"
            }, ensure_ascii=False, indent=2)

        simplified_paths = []
        for path in paths[:3]:
            steps = []
            for step in path.get("steps", [])[:30]:
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
                "restriction": path.get("restriction"),
                "steps": steps
            })

        result = {
            "status": "success",
            "mode": "truck",
            "origin": origin,
            "destination": destination,
            "truck_params": {
                "type": truck_type,
                "weight_t": weight,
                "height_m": height,
                "width_m": width,
                "load_weight_t": load_weight,
                "axis": axis
            },
            "routes": simplified_paths
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
