from typing import Any, Dict
import json
import time
from functools import lru_cache
from threading import Lock

from .skill_registry import SkillRegistry
from .base_skill import BaseSkill


class SkillInvoker:
    """
    技能调用器，负责技能的调用、缓存、限流等
    """

    def __init__(self):
        self._skill_instances: Dict[str, BaseSkill] = {}
        self._cache = {}
        self._cache_lock = Lock()
        self._call_counts = {}
        self._rate_limit = 100  # 每分钟最多调用次数
        self._window_start = time.time()

    def _get_skill_instance(self, skill_name: str) -> BaseSkill:
        """
        获取技能实例，懒加载
        """
        if skill_name not in self._skill_instances:
            skill_class = SkillRegistry.get_skill(skill_name)
            self._skill_instances[skill_name] = skill_class()
        return self._skill_instances[skill_name]

    def _check_rate_limit(self) -> None:
        """
        检查调用频率，超过限制抛出异常
        """
        now = time.time()
        if now - self._window_start > 60:
            self._window_start = now
            self._call_counts.clear()

        current_count = self._call_counts.get("total", 0)
        if current_count >= self._rate_limit:
            raise RuntimeError("技能调用频率超过限制，请稍后再试")

        self._call_counts["total"] = current_count + 1

    def _get_cache_key(self, skill_name: str, params: Dict[str, Any]) -> str:
        """
        生成缓存键
        """
        sorted_params = json.dumps(params, sort_keys=True)
        return f"{skill_name}:{sorted_params}"

    async def invoke(
        self,
        skill_name: str,
        params: Dict[str, Any],
        use_cache: bool = True,
        cache_ttl: int = 300  # 缓存有效期，默认5分钟
    ) -> str:
        """
        调用技能
        :param skill_name: 技能名称
        :param params: 技能参数
        :param use_cache: 是否使用缓存
        :param cache_ttl: 缓存有效期（秒）
        :return: 技能执行结果（JSON字符串）
        """
        # 检查频率限制
        self._check_rate_limit()

        # 检查缓存
        cache_key = self._get_cache_key(skill_name, params)
        if use_cache and cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if time.time() - cache_entry["timestamp"] < cache_ttl:
                return cache_entry["result"]

        # 获取技能实例
        skill = self._get_skill_instance(skill_name)

        # 验证参数
        skill.validate_parameters(params)

        # 执行技能
        result = await skill.execute(**params)

        # 缓存结果
        if use_cache:
            with self._cache_lock:
                self._cache[cache_key] = {
                    "result": result,
                    "timestamp": time.time()
                }

        return result

    def clear_cache(self, skill_name: str = None) -> None:
        """
        清除缓存
        :param skill_name: 可选，指定清除某个技能的缓存，否则清除所有
        """
        with self._cache_lock:
            if skill_name:
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{skill_name}:")]
                for key in keys_to_remove:
                    del self._cache[key]
            else:
                self._cache.clear()


# 全局技能调用器实例
skill_invoker = SkillInvoker()
