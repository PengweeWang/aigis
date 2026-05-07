from typing import Optional, Dict, Any, List
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class BatchGeocodeSkill(BaseSkill):
    name = "batch_geocode"
    description = "批量将结构化地址转换为经纬度坐标，一次最多处理10个地址"
    parameters = [
        {
            "name": "addresses",
            "type": "array",
            "description": "地址列表，每个元素为字符串，最多10个地址",
            "required": True
        },
        {
            "name": "city",
            "type": "string",
            "description": "默认城市名/拼音/citycode/adcode，可选",
            "required": False
        }
    ]

    async def execute(self, addresses: List[str], city: Optional[str] = None) -> str:
        if not addresses or len(addresses) == 0:
            raise ValueError("地址列表不能为空")
        if len(addresses) > 10:
            raise ValueError("一次最多处理10个地址，请分批调用")

        results = []
        for address in addresses:
            params: Dict[str, Any] = {"address": address, "output": "JSON"}
            if city:
                params["city"] = city

            try:
                data = await amap_get("/v3/geocode/geo", params)
                geocodes = data.get("geocodes", [])
                if geocodes:
                    geo = geocodes[0]
                    location = geo.get("location", "")
                    lng, lat = (location.split(",") + ["", ""])[:2]
                    results.append({
                        "address": address,
                        "status": "success",
                        "formatted_address": geo.get("formatted_address"),
                        "location": location,
                        "longitude": float(lng) if lng else None,
                        "latitude": float(lat) if lat else None,
                        "adcode": geo.get("adcode"),
                        "level": geo.get("level")
                    })
                else:
                    results.append({
                        "address": address,
                        "status": "not_found",
                        "message": "未找到匹配的地理编码结果"
                    })
            except Exception as e:
                results.append({
                    "address": address,
                    "status": "error",
                    "message": str(e)
                })

        success_count = sum(1 for r in results if r["status"] == "success")
        out = {
            "status": "success",
            "total": len(addresses),
            "success_count": success_count,
            "fail_count": len(addresses) - success_count,
            "results": results
        }

        return json.dumps(out, ensure_ascii=False, indent=2)
