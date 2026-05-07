"""
技能单元测试 - 验证各技能的参数校验和基本逻辑
"""

import pytest
import json
from unittest.mock import AsyncMock, patch

from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import SkillRegistry, register_skill, load_all_skills
from amap_skill.core.skill_invoker import SkillInvoker


# ============================================================
# 基础框架测试
# ============================================================

class TestBaseSkill:
    """技能基类测试"""

    def test_validate_required_params(self):
        """测试必选参数校验"""

        @register_skill
        class TestSkill(BaseSkill):
            name = "test_required_param"
            description = "test"
            parameters = [
                {"name": "required_field", "type": "string", "required": True}
            ]

            async def execute(self, **kwargs):
                return json.dumps({"status": "ok"})

        skill = TestSkill()

        # 缺少必选参数应抛出异常
        with pytest.raises(ValueError, match="缺少必选参数"):
            skill.validate_parameters({})

        # 提供必选参数应通过
        skill.validate_parameters({"required_field": "value"})

    def test_validate_param_types(self):
        """测试参数类型校验"""

        @register_skill
        class TestTypeSkill(BaseSkill):
            name = "test_type_param"
            description = "test"
            parameters = [
                {"name": "count", "type": "integer", "required": True},
                {"name": "name", "type": "string", "required": False}
            ]

            async def execute(self, **kwargs):
                return json.dumps({"status": "ok"})

        skill = TestTypeSkill()

        # 类型正确
        skill.validate_parameters({"count": 10})

        # 类型错误
        with pytest.raises(ValueError, match="类型错误"):
            skill.validate_parameters({"count": "not_a_number"})


class TestSkillRegistry:
    """技能注册器测试"""

    def setup_method(self):
        SkillRegistry.clear()

    def test_register_skill(self):
        """测试技能注册"""

        @register_skill
        class SampleSkill(BaseSkill):
            name = "sample_skill"
            description = "sample"
            parameters = []

            async def execute(self, **kwargs):
                return json.dumps({"status": "ok"})

        assert "sample_skill" in SkillRegistry._skills
        assert SkillRegistry.get_skill("sample_skill") == SampleSkill

    def test_register_duplicate_skill(self):
        """测试重复注册"""

        @register_skill
        class DupSkill1(BaseSkill):
            name = "dup_skill"
            description = "dup1"
            parameters = []

            async def execute(self, **kwargs):
                return json.dumps({"status": "ok"})

        with pytest.raises(ValueError, match="已经存在"):

            @register_skill
            class DupSkill2(BaseSkill):
                name = "dup_skill"
                description = "dup2"
                parameters = []

                async def execute(self, **kwargs):
                    return json.dumps({"status": "ok"})

    def test_get_nonexistent_skill(self):
        """测试获取不存在的技能"""
        with pytest.raises(ValueError, match="不存在"):
            SkillRegistry.get_skill("nonexistent_skill")

    def test_register_non_subclass(self):
        """测试注册非BaseSkill子类"""
        with pytest.raises(TypeError, match="必须继承自 BaseSkill"):
            SkillRegistry.register(object)


# ============================================================
# POI技能测试
# ============================================================

class TestPoiKeywordSearchSkill:
    """POI关键词搜索技能测试"""

    def test_parameters_defined(self):
        """测试参数定义完整"""
        from amap_skill.skills.poi.poi_keyword_search import PoiKeywordSearchSkill
        skill = PoiKeywordSearchSkill()
        assert skill.name == "poi_keyword_search"
        assert len(skill.parameters) >= 1
        required_params = [p for p in skill.parameters if p.get("required")]
        assert any(p["name"] == "keywords" for p in required_params)

    @pytest.mark.asyncio
    async def test_execute_with_mock(self):
        """测试技能执行（mock API）"""
        from amap_skill.skills.poi.poi_keyword_search import PoiKeywordSearchSkill

        mock_response = {
            "status": "1",
            "count": "2",
            "pois": [
                {
                    "id": "B000A83M61",
                    "name": "星巴克(三里屯店)",
                    "type": "餐饮服务;咖啡厅",
                    "address": "北京市朝阳区三里屯路19号",
                    "location": "116.454617,39.934006",
                    "distance": [],
                    "tel": "010-64176978",
                    "business_area": "三里屯"
                },
                {
                    "id": "B000A8UMI8",
                    "name": "漫咖啡(三里屯店)",
                    "type": "餐饮服务;咖啡厅",
                    "address": "北京市朝阳区三里屯北街81号",
                    "location": "116.455724,39.936223",
                    "distance": [],
                    "tel": "010-64165528",
                    "business_area": "三里屯"
                }
            ]
        }

        with patch("amap_skill.skills.poi.poi_keyword_search.amap_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            skill = PoiKeywordSearchSkill()
            result = await skill.execute(keywords="咖啡店", city="北京")
            data = json.loads(result)

            assert data["status"] == "success"
            assert data["count"] == 2
            assert len(data["pois"]) == 2
            assert data["pois"][0]["name"] == "星巴克(三里屯店)"


class TestPoiAroundSearchSkill:
    """POI周边搜索技能测试"""

    def test_parameters_defined(self):
        from amap_skill.skills.poi.poi_around_search import PoiAroundSearchSkill
        skill = PoiAroundSearchSkill()
        assert skill.name == "poi_around_search"
        required_params = [p for p in skill.parameters if p.get("required")]
        assert any(p["name"] == "location" for p in required_params)


# ============================================================
# 路径规划技能测试
# ============================================================

class TestPublicTransitPlanningSkill:
    """公交路径规划技能测试"""

    def test_invalid_strategy(self):
        from amap_skill.skills.route.public_transit_planning import PublicTransitPlanningSkill
        skill = PublicTransitPlanningSkill()
        with pytest.raises(ValueError, match="strategy"):
            import asyncio
            asyncio.run(skill.execute(
                origin="116.461,39.909",
                destination="116.318,39.982",
                city="北京",
                strategy=99
            ))

    def test_parameters_defined(self):
        from amap_skill.skills.route.public_transit_planning import PublicTransitPlanningSkill
        skill = PublicTransitPlanningSkill()
        assert skill.name == "public_transit_planning"
        required_params = [p for p in skill.parameters if p.get("required")]
        required_names = [p["name"] for p in required_params]
        assert "origin" in required_names
        assert "destination" in required_names
        assert "city" in required_names


class TestTruckPlanningSkill:
    """货车路径规划技能测试"""

    def test_parameters_defined(self):
        from amap_skill.skills.route.truck_planning import TruckPlanningSkill
        skill = TruckPlanningSkill()
        assert skill.name == "truck_planning"
        required_params = [p for p in skill.parameters if p.get("required")]
        required_names = [p["name"] for p in required_params]
        assert "origin" in required_names
        assert "destination" in required_names


# ============================================================
# 地图交互技能测试
# ============================================================

class TestDistrictSearchSkill:
    """行政区域查询技能测试"""

    def test_parameters_defined(self):
        from amap_skill.skills.map.district_search import DistrictSearchSkill
        skill = DistrictSearchSkill()
        assert skill.name == "district_search"
        required_params = [p for p in skill.parameters if p.get("required")]
        assert any(p["name"] == "keywords" for p in required_params)

    @pytest.mark.asyncio
    async def test_invalid_extensions(self):
        from amap_skill.skills.map.district_search import DistrictSearchSkill
        skill = DistrictSearchSkill()
        with pytest.raises(ValueError, match="extensions"):
            await skill.execute(keywords="北京", extensions="invalid")


class TestWeatherSearchSkill:
    """天气查询技能测试"""

    @pytest.mark.asyncio
    async def test_execute_with_mock(self):
        from amap_skill.skills.map.weather_search import WeatherSearchSkill

        mock_response = {
            "status": "1",
            "lives": [
                {
                    "province": "北京",
                    "city": "朝阳区",
                    "adcode": "110105",
                    "weather": "晴",
                    "temperature": "25",
                    "winddirection": "北",
                    "windpower": "≤3",
                    "humidity": "32",
                    "reporttime": "2025-05-06 14:32:18"
                }
            ]
        }

        with patch("amap_skill.skills.map.weather_search.amap_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            skill = WeatherSearchSkill()
            result = await skill.execute(city="北京", extensions="base")
            data = json.loads(result)

            assert data["status"] == "success"
            assert data["type"] == "live"
            assert data["weather"] == "晴"
            assert data["temperature"] == "25"


class TestCoordinateConvertSkill:
    """坐标转换技能测试"""

    def test_invalid_coordsys(self):
        from amap_skill.skills.map.coordinate_convert import CoordinateConvertSkill
        skill = CoordinateConvertSkill()
        with pytest.raises(ValueError, match="coordsys"):
            import asyncio
            asyncio.run(skill.execute(locations="116.397,39.909", coordsys="invalid"))

    def test_too_many_locations(self):
        from amap_skill.skills.map.coordinate_convert import CoordinateConvertSkill
        skill = CoordinateConvertSkill()
        locations = "|".join([f"116.{i},39.{i}" for i in range(50)])
        with pytest.raises(ValueError, match="最多转换40个"):
            import asyncio
            asyncio.run(skill.execute(locations=locations, coordsys="gps"))


# ============================================================
# 技能调用器测试
# ============================================================

class TestSkillInvoker:
    """技能调用器测试"""

    def setup_method(self):
        SkillRegistry.clear()

    @pytest.mark.asyncio
    async def test_invoke_skill(self):
        """测试技能调用"""

        @register_skill
        class InvokeTestSkill(BaseSkill):
            name = "invoke_test"
            description = "test invoke"
            parameters = [
                {"name": "msg", "type": "string", "required": True}
            ]

            async def execute(self, msg="hello"):
                return json.dumps({"echo": msg})

        invoker = SkillInvoker()
        result = await invoker.invoke("invoke_test", {"msg": "world"})
        data = json.loads(result)
        assert data["echo"] == "world"

    @pytest.mark.asyncio
    async def test_invoke_with_cache(self):
        """测试缓存功能"""

        call_count = 0

        @register_skill
        class CacheTestSkill(BaseSkill):
            name = "cache_test"
            description = "test cache"
            parameters = []

            async def execute(self):
                nonlocal call_count
                call_count += 1
                return json.dumps({"count": call_count})

        invoker = SkillInvoker()
        await invoker.invoke("cache_test", {}, use_cache=True)
        await invoker.invoke("cache_test", {}, use_cache=True)

        # 第二次调用应使用缓存，不应增加调用次数
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_invoke_missing_required_param(self):
        """测试缺少必选参数"""

        @register_skill
        class RequiredTestSkill(BaseSkill):
            name = "required_test"
            description = "test required"
            parameters = [
                {"name": "must_have", "type": "string", "required": True}
            ]

            async def execute(self, **kwargs):
                return json.dumps({"status": "ok"})

        invoker = SkillInvoker()
        with pytest.raises(ValueError, match="缺少必选参数"):
            await invoker.invoke("required_test", {})
