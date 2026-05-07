"""
Amap Skill 扩展库
提供基于高德地图 API 的各种 GIS 功能技能
"""

from .core.base_skill import BaseSkill
from .core.skill_registry import register_skill, load_all_skills, SkillRegistry
from .core.skill_invoker import skill_invoker, SkillInvoker

__version__ = "0.1.0"
__all__ = [
    "BaseSkill",
    "register_skill",
    "load_all_skills",
    "SkillRegistry",
    "skill_invoker",
    "SkillInvoker"
]
