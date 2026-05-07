from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseSkill(ABC):
    """
    所有技能的基类
    """

    # 技能唯一标识
    name: str = ""

    # 技能描述
    description: str = ""

    # 技能参数定义，格式示例：
    # [
    #     {
    #         "name": "param_name",
    #         "type": "string",
    #         "description": "参数描述",
    #         "required": True
    #     }
    # ]
    parameters: List[Dict[str, Any]] = []

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """
        执行技能的核心逻辑
        返回 JSON 格式的字符串结果
        """
        pass

    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """
        验证参数是否符合要求
        抛出 ValueError 如果参数不合法
        """
        # 检查必选参数
        for param in self.parameters:
            if param.get("required", False) and param["name"] not in params:
                raise ValueError(f"缺少必选参数: {param['name']}")

        # 检查参数类型
        for param_name, value in params.items():
            param_def = next((p for p in self.parameters if p["name"] == param_name), None)
            if not param_def:
                continue  # 忽略未知参数

            expected_type = param_def.get("type")
            if not expected_type:
                continue

            # 简单类型检查
            type_map = {
                "string": str,
                "integer": int,
                "number": (int, float),
                "boolean": bool,
                "array": list,
                "object": dict
            }

            if expected_type in type_map:
                expected_types = type_map[expected_type]
                if not isinstance(value, expected_types):
                    raise ValueError(
                        f"参数 {param_name} 类型错误，期望 {expected_type}，实际 {type(value).__name__}"
                    )
