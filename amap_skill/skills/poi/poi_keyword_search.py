from typing import Optional, Dict, Any
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class PoiKeywordSearchSkill(BaseSkill):
    name = "poi_keyword_search"
    description = "根据关键词搜索POI兴趣点，支持按城市和类型筛选"
    parameters = [
        {
            "name": "keywords",
            "type": "string",
            "description": "搜索关键词，多个关键词用|分隔",
            "required": True
        },
        {
            "name": "city",
            "type": "string",
            "description": "城市名、拼音、citycode或adcode，可选",
            "required": False
        },
        {
            "name": "types",
            "type": "string",
            "description": "POI类型，多个类型用|分隔，可选",
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
        keywords: str,
        city: Optional[str] = None,
        types: Optional[str] = None,
        page_size: int = 20,
        page_num: int = 1
    ) -> str:
        params: Dict[str, Any] = {
            "keywords": keywords,
            "output": "JSON",
            "page_size": max(1, min(page_size, 50)),
            "page_num": max(1, page_num)
        }

        if city:
            params["city"] = city
            params["citylimit"] = True  # 限制只返回指定城市的结果

        if types:
            params["types"] = types

        data = await amap_get("/v3/place/text", params)

        # 精简返回结果
        pois = data.get("pois", [])
        simplified_pois = []
        for poi in pois[:20]:  # 最多返回20条结果
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
            "page_size": page_size,
            "page_num": page_num,
            "pois": simplified_pois
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
