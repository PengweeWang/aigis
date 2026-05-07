from typing import Dict, Any
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class StaticMapSkill(BaseSkill):
    name = "static_map"
    description = "生成静态地图图片URL，支持标注点、路线、区域等叠加，无需JS API即可展示地图"
    parameters = [
        {
            "name": "location",
            "type": "string",
            "description": "地图中心点，格式：经度,纬度",
            "required": True
        },
        {
            "name": "zoom",
            "type": "integer",
            "description": "缩放级别，3-18，默认11",
            "required": False
        },
        {
            "name": "size",
            "type": "string",
            "description": "图片尺寸，格式：宽*高，默认400*300，最大1024*1024",
            "required": False
        },
        {
            "name": "markers",
            "type": "string",
            "description": "标注点，格式：经度,纬度,名称 多个用|分隔，可选",
            "required": False
        },
        {
            "name": "paths",
            "type": "string",
            "description": "路线，格式：经度,纬度,经度,纬度,... 可选",
            "required": False
        }
    ]

    async def execute(
        self,
        location: str,
        zoom: int = 11,
        size: str = "400*300",
        markers: str = "",
        paths: str = ""
    ) -> str:
        params: Dict[str, Any] = {
            "location": location,
            "zoom": max(3, min(zoom, 18)),
            "size": size,
            "output": "JSON"
        }

        if markers:
            params["markers"] = markers
        if paths:
            params["paths"] = paths

        data = await amap_get("/v3/staticmap", params)

        # 静态地图API返回的是图片URL
        result = {
            "status": "success",
            "image_url": f"{AMAP_BASE_URL}/v3/staticmap?" + "&".join(
                f"{k}={v}" for k, v in params.items() if k != "output"
            ),
            "location": location,
            "zoom": zoom,
            "size": size
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
