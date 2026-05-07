from typing import Dict, Any
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class IpLocationSkill(BaseSkill):
    name = "ip_location"
    description = "根据IP地址查询地理位置信息，包括省份、城市、行政区编码等"
    parameters = [
        {
            "name": "ip",
            "type": "string",
            "description": "IP地址，例如：114.247.50.2。不填则查询当前请求的IP",
            "required": False
        }
    ]

    async def execute(self, ip: str = "") -> str:
        params: Dict[str, Any] = {"output": "JSON"}
        if ip:
            params["ip"] = ip

        data = await amap_get("/v3/ip", params)

        result = {
            "status": "success",
            "ip": data.get("ip", ip),
            "province": data.get("province"),
            "city": data.get("city"),
            "adcode": data.get("adcode"),
            "rectangle": data.get("rectangle")
        }

        if not result["province"] and not result["city"]:
            result["status"] = "not_found"
            result["message"] = f"未找到IP {ip} 的位置信息"

        return json.dumps(result, ensure_ascii=False, indent=2)
