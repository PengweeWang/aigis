"""
Amap Skill REST API 服务

独立的轻量级 API 服务，直接暴露所有高德地图技能接口。
不依赖 opencode，可以独立运行。

启动方式:
    python -m amap_skill.api_server

接口列表:
    GET  /skills              - 列出所有可用技能
    POST /skill/{name}        - 调用指定技能
    GET  /health              - 健康检查

调用示例:
    # 查询可用技能
    curl http://localhost:5050/skills

    # 天气查询
    curl -X POST http://localhost:5050/skill/weather_search \
      -H 'Content-Type: application/json' \
      -d '{"city": "北京", "extensions": "base"}'

    # POI搜索
    curl -X POST http://localhost:5050/skill/poi_keyword_search \
      -H 'Content-Type: application/json' \
      -d '{"keywords": "咖啡店", "city": "北京"}'

    # 地理编码
    curl -X POST http://localhost:5050/skill/geocode \
      -H 'Content-Type: application/json' \
      -d '{"address": "北京市朝阳区阜通东大街6号"}'

    # 行政区域查询
    curl -X POST http://localhost:5050/skill/district_search \
      -H 'Content-Type: application/json' \
      -d '{"keywords": "上海", "subdistrict": 1}'

    # 路径规划
    curl -X POST http://localhost:5050/skill/route_planning \
      -H 'Content-Type: application/json' \
      -d '{"origin": "116.397428,39.90923", "destination": "116.274722,39.998056", "mode": "driving"}'

    # 坐标转换
    curl -X POST http://localhost:5050/skill/coordinate_convert \
      -H 'Content-Type: application/json' \
      -d '{"locations": "116.397428,39.90923", "coordsys": "gps"}'
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

# 确保项目根目录在 sys.path 中
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 加载 .env
from amap_mcp.server import _load_env_file, get_amap_key

_load_env_file()

from amap_mcp.server import amap_get, geocode, reverse_geocode, route_planning, distance_measure
from amap_skill import load_all_skills

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ImportError:
    print("缺少依赖，请安装: uv pip install fastapi uvicorn")
    sys.exit(1)

app = FastAPI(title="Amap Skill API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加载技能
skills = load_all_skills()
skill_map: Dict[str, Any] = {s.name: s for s in skills}

# 同时注册原有 MCP 工具
builtin_tools = {
    "geocode": geocode,
    "reverse_geocode": reverse_geocode,
    "route_planning": route_planning,
    "distance_measure": distance_measure,
}


class SkillRequest(BaseModel):
    """技能调用请求 - 任意参数通过 extra fields 传入"""
    class Config:
        extra = "allow"


@app.get("/health")
async def health():
    key_status = "configured" if get_amap_key() else "missing"
    return {
        "status": "healthy",
        "amap_api_key": key_status,
        "skills_count": len(skill_map) + len(builtin_tools),
    }


@app.get("/skills")
async def list_skills():
    """列出所有可用技能"""
    result = []
    for name, skill in skill_map.items():
        params = []
        for p in skill.parameters:
            params.append({
                "name": p["name"],
                "type": p.get("type", "string"),
                "required": p.get("required", False),
                "description": p.get("description", ""),
            })
        result.append({
            "name": name,
            "description": skill.description,
            "parameters": params,
            "source": "amap_skill",
        })

    for name, fn in builtin_tools.items():
        result.append({
            "name": name,
            "description": fn.__doc__ or "",
            "parameters": "see MCP tool definition",
            "source": "builtin",
        })

    return {"count": len(result), "skills": result}


@app.post("/skill/{skill_name}")
async def call_skill(skill_name: str, request: Dict[str, Any] = None):
    """调用指定技能"""
    request = request or {}

    # 先查 builtin 工具
    if skill_name in builtin_tools:
        try:
            result = await builtin_tools[skill_name](**request)
            return {"status": "success", "skill": skill_name, "result": json.loads(result)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # 再查 amap_skill
    if skill_name not in skill_map:
        raise HTTPException(status_code=404, detail=f"技能 '{skill_name}' 不存在，可用技能: {list(skill_map.keys()) + list(builtin_tools.keys())}")

    skill = skill_map[skill_name]
    try:
        result = await skill.execute(**request)
        return {"status": "success", "skill": skill_name, "result": json.loads(result)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    port = int(os.getenv("AMAP_SKILL_PORT", "5050"))
    print(f"Amap Skill API 启动于 http://localhost:{port}")
    print(f"已注册 {len(skill_map) + len(builtin_tools)} 个技能")
    print(f"接口文档: http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
