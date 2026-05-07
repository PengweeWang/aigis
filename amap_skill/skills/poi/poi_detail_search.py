from typing import Dict, Any
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class PoiDetailSearchSkill(BaseSkill):
    name = "poi_detail_search"
    description = "根据POI的ID查询详细信息，包括名称、地址、电话、评分、营业时间、图片等"
    parameters = [
        {
            "name": "poi_id",
            "type": "string",
            "description": "POI的唯一标识ID，可从关键词搜索或周边搜索结果中获取",
            "required": True
        }
    ]

    async def execute(self, poi_id: str) -> str:
        params: Dict[str, Any] = {
            "id": poi_id,
            "output": "JSON"
        }

        data = await amap_get("/v3/place/detail", params)
        pois = data.get("pois", [])

        if not pois:
            return json.dumps({
                "status": "not_found",
                "poi_id": poi_id,
                "message": f"未找到ID为 {poi_id} 的POI"
            }, ensure_ascii=False, indent=2)

        poi = pois[0]
        result = {
            "status": "success",
            "id": poi.get("id"),
            "name": poi.get("name"),
            "type": poi.get("type"),
            "address": poi.get("address"),
            "location": poi.get("location"),
            "tel": poi.get("tel"),
            "rating": poi.get("rating"),
            "cost": poi.get("biz_ext", {}).get("cost"),
            "open_time": poi.get("biz_ext", {}).get("open_time"),
            "business_area": poi.get("business_area"),
            "photos": [p.get("url") for p in (poi.get("photos") or [])[:5]],
            "indoor_map": poi.get("indoor_data", {}),
            "parking_type": poi.get("parking_type"),
            "alias": poi.get("alias"),
            "description": poi.get("description")
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
