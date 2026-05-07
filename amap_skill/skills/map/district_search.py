from typing import Optional, Dict, Any
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class DistrictSearchSkill(BaseSkill):
    name = "district_search"
    description = "查询行政区域信息，包括区域编码、中心点、边界范围、下级行政区划等"
    parameters = [
        {
            "name": "keywords",
            "type": "string",
            "description": "查询关键字，例如：北京、朝阳、110000等",
            "required": True
        },
        {
            "name": "subdistrict",
            "type": "integer",
            "description": "子行政区级数：0-不返回子级，1-返回下一级，2-返回下两级，3-返回下三级",
            "required": False
        },
        {
            "name": "extensions",
            "type": "string",
            "description": "返回结果级别：base-基础信息，all-包含边界坐标等",
            "required": False
        }
    ]

    async def execute(
        self,
        keywords: str,
        subdistrict: int = 1,
        extensions: str = "base"
    ) -> str:
        if extensions not in {"base", "all"}:
            raise ValueError("extensions 必须为 'base' 或 'all'")
        if subdistrict not in {0, 1, 2, 3}:
            raise ValueError("subdistrict 必须为 0、1、2 或 3")

        params: Dict[str, Any] = {
            "keywords": keywords,
            "subdistrict": subdistrict,
            "extensions": extensions,
            "output": "JSON"
        }

        data = await amap_get("/v3/config/district", params)
        districts = data.get("districts", [])

        if not districts:
            return json.dumps({
                "status": "not_found",
                "keywords": keywords,
                "message": f"未找到与 '{keywords}' 匹配的行政区域"
            }, ensure_ascii=False, indent=2)

        def simplify_district(d: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
            out: Dict[str, Any] = {
                "adcode": d.get("adcode"),
                "name": d.get("name"),
                "center": d.get("center"),
                "level": d.get("level"),
            }
            if extensions == "all":
                out["polyline"] = d.get("polyline")
            children = d.get("districts", [])
            if children and depth < subdistrict:
                out["districts"] = [simplify_district(c, depth + 1) for c in children]
            return out

        simplified = [simplify_district(d) for d in districts]

        result = {
            "status": "success",
            "keywords": keywords,
            "count": len(simplified),
            "districts": simplified
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
