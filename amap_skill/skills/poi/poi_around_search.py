from typing import Optional, Dict, Any
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class PoiAroundSearchSkill(BaseSkill):
    name = "poi_around_search"
    description = "根据中心点坐标搜索周边POI兴趣点，支持按关键词和类型筛选"
    parameters = [
        {
            "name": "location",
            "type": "string",
            "description": "中心点坐标，格式：经度,纬度，例如116.397428,39.90923",
            "required": True
        },
        {
            "name": "radius",
            "type": "integer",
            "description": "搜索半径，单位米，默认3000，最大50000",
            "required": False
        },
        {
            "name": "keywords",
            "type": "string",
            "description": "搜索关键词，多个用|分隔，可选",
            "required": False
        },
        {
            "name": "types",
            "type": "string",
            "description": "POI类型，多个用|分隔，可选。常见类型：餐饮服务|购物服务|生活服务|体育休闲服务|医疗保健服务|住宿服务|风景名胜|商务住宅|政府机构|科教文化服务|交通设施服务|金融保险服务|公司企业",
            "required": False
        },
        {
            "name": "page_size",
            "type": "integer",
            "description": "每页返回结果数量，默认20，最大50",
            "required": False
        },
        {
            "name": "page_num",
            "type": "integer",
            "description": "页码，默认1",
            "required": False
        }
    ]

    async def execute(
        self,
        location: str,
        radius: int = 3000,
        keywords: Optional[str] = None,
        types: Optional[str] = None,
        page_size: int = 20,
        page_num: int = 1
    ) -> str:
        params: Dict[str, Any] = {
            "location": location,
            "radius": max(1, min(radius, 50000)),
            "output": "JSON",
            "page_size": max(1, min(page_size, 50)),
            "page_num": max(1, page_num)
        }

        if keywords:
            params["keywords"] = keywords
        if types:
            params["types"] = types

        data = await amap_get("/v3/place/around", params)

        pois = data.get("pois", [])
        simplified_pois = []
        for poi in pois[:20]:
            simplified_pois.append({
                "id": poi.get("id"),
                "name": poi.get("name"),
                "type": poi.get("type"),
                "address": poi.get("address"),
                "location": poi.get("location"),
                "distance": poi.get("distance"),
                "tel": poi.get("tel"),
                "business_area": poi.get("business_area")
            })

        result = {
            "status": "success",
            "count": int(data.get("count", 0)),
            "radius_m": radius,
            "page_size": page_size,
            "page_num": page_num,
            "pois": simplified_pois
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
