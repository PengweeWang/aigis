import importlib
import os
from pathlib import Path
from typing import Dict, Type, List

from .base_skill import BaseSkill


class SkillRegistry:
    """
    技能注册器，管理所有已注册的技能
    """

    _skills: Dict[str, Type[BaseSkill]] = {}

    @classmethod
    def register(cls, skill_class: Type[BaseSkill]) -> None:
        """
        注册一个技能类
        """
        if not issubclass(skill_class, BaseSkill):
            raise TypeError(f"{skill_class.__name__} 必须继承自 BaseSkill")

        if not skill_class.name:
            raise ValueError(f"技能 {skill_class.__name__} 必须设置 name 属性")

        if skill_class.name in cls._skills:
            raise ValueError(f"技能 {skill_class.name} 已经存在")

        cls._skills[skill_class.name] = skill_class

    @classmethod
    def get_skill(cls, name: str) -> Type[BaseSkill]:
        """
        根据名称获取技能类
        """
        if name not in cls._skills:
            raise ValueError(f"技能 {name} 不存在")
        return cls._skills[name]

    @classmethod
    def get_all_skills(cls) -> List[Type[BaseSkill]]:
        """
        获取所有已注册的技能类
        """
        return list(cls._skills.values())

    @classmethod
    def clear(cls) -> None:
        """
        清空所有注册的技能（主要用于测试）
        """
        cls._skills.clear()


def register_skill(skill_class: Type[BaseSkill]) -> Type[BaseSkill]:
    """
    技能注册装饰器
    使用示例:
        @register_skill
        class MySkill(BaseSkill):
            name = "my_skill"
            # ...
    """
    SkillRegistry.register(skill_class)
    return skill_class


def load_all_skills() -> List[BaseSkill]:
    """
    自动加载 skills 目录下的所有技能
    返回技能实例列表
    """
    skills_dir = Path(__file__).parent.parent / "skills"

    # 遍历所有 Python 文件
    for root, _, files in os.walk(skills_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("_"):
                # 构建模块路径
                file_path = Path(root) / file
                relative_path = file_path.relative_to(skills_dir.parent)
                module_path = str(relative_path).replace(".py", "").replace(os.sep, ".")

                # 导入模块
                importlib.import_module(f"amap_skill.{module_path}")

    # 实例化所有技能
    skill_instances = []
    for skill_class in SkillRegistry.get_all_skills():
        skill_instances.append(skill_class())

    return skill_instances
