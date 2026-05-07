from typing import Dict, Any
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class CoordinateConvertSkill(BaseSkill):
    name = "coordinate_convert"
    description = "将非高德坐标系（GPS/WGS84、百度/BG-09、Mapbar）的坐标转换为高德坐标系（GCJ-02）"
    parameters = [
        {
            "name": "locations",
            "type": "string",
            "description": "待转换的坐标，格式：经度,纬度。多个坐标用|分隔，最多支持40个",
            "required": True
        },
        {
            "name": "coordsys",
            "type": "string",
            "description": "源坐标系：gps-谷歌/国际GPS坐标系，baidu-百度坐标系，mapbar-Mapbar坐标系",
            "required": True
        }
    ]

    async def execute(self, locations: str, coordsys: str = "gps") -> str:
        valid_coordsys = {"gps", "baidu", "mapbar"}
        if coordsys not in valid_coordsys:
            raise ValueError(f"coordsys 必须为 {', '.join(valid_coordsys)} 之一")

        coord_list = locations.split("|")
        if len(coord_list) > 40:
            raise ValueError("一次最多转换40个坐标，请分批调用")

        params: Dict[str, Any] = {
            "locations": locations,
            "coordsys": coordsys,
            "output": "JSON"
        }

        data = await amap_get("/v3/assistant/coordinate/convert", params)
        converted = data.get("locations", "")

        converted_coords = []
        for pair in converted.split(";"):
            pair = pair.strip()
            if not pair:
                continue
            parts = pair.split(",")
            if len(parts) == 2:
                try:
                    converted_coords.append({
                        "longitude": float(parts[0]),
                        "latitude": float(parts[1])
                    })
                except ValueError:
                    continue

        result = {
            "status": "success",
            "source_coordsys": coordsys,
            "target_coordsys": "gcj02",
            "input_count": len(coord_list),
            "output_count": len(converted_coords),
            "locations": converted_coords
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
