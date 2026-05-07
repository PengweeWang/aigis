from typing import Dict, Any
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get


@register_skill
class WeatherSearchSkill(BaseSkill):
    name = "weather_search"
    description = "查询指定城市的天气信息，支持实时天气和未来天气预报"
    parameters = [
        {
            "name": "city",
            "type": "string",
            "description": "城市名称或adcode，例如：北京、110000、朝阳区",
            "required": True
        },
        {
            "name": "extensions",
            "type": "string",
            "description": "返回类型：base-实况天气，all-包含未来天气预报",
            "required": False
        }
    ]

    async def execute(self, city: str, extensions: str = "base") -> str:
        if extensions not in {"base", "all"}:
            raise ValueError("extensions 必须为 'base' 或 'all'")

        params: Dict[str, Any] = {
            "city": city,
            "extensions": extensions,
            "output": "JSON"
        }

        data = await amap_get("/v3/weather/weatherInfo", params)

        if extensions == "base":
            lives = data.get("lives", [])
            if not lives:
                return json.dumps({
                    "status": "not_found",
                    "city": city,
                    "message": f"未找到 '{city}' 的天气信息"
                }, ensure_ascii=False, indent=2)

            weather = lives[0]
            result = {
                "status": "success",
                "type": "live",
                "province": weather.get("province"),
                "city": weather.get("city"),
                "adcode": weather.get("adcode"),
                "weather": weather.get("weather"),
                "temperature": weather.get("temperature"),
                "wind_direction": weather.get("winddirection"),
                "wind_power": weather.get("windpower"),
                "humidity": weather.get("humidity"),
                "report_time": weather.get("reporttime")
            }
        else:
            forecasts = data.get("forecasts", [])
            if not forecasts:
                return json.dumps({
                    "status": "not_found",
                    "city": city,
                    "message": f"未找到 '{city}' 的天气预报信息"
                }, ensure_ascii=False, indent=2)

            forecast = forecasts[0]
            casts = []
            for cast in forecast.get("casts", []):
                casts.append({
                    "date": cast.get("date"),
                    "week": cast.get("week"),
                    "day_weather": cast.get("dayweather"),
                    "night_weather": cast.get("nightweather"),
                    "day_temp": cast.get("daytemp"),
                    "night_temp": cast.get("nighttemp"),
                    "day_wind": cast.get("daywind"),
                    "night_wind": cast.get("nightwind"),
                    "day_power": cast.get("daypower"),
                    "night_power": cast.get("nightpower")
                })

            result = {
                "status": "success",
                "type": "forecast",
                "province": forecast.get("province"),
                "city": forecast.get("city"),
                "adcode": forecast.get("adcode"),
                "report_time": forecast.get("reporttime"),
                "casts": casts
            }

        return json.dumps(result, ensure_ascii=False, indent=2)
