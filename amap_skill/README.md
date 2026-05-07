# Amap Skill 扩展库

基于高德地图 API 的可扩展技能库，为 opencode 智能体提供丰富的 GIS 功能支持。

## 目录结构

```
amap_skill/
├── docs/                    # 文档目录
│   ├── improvement_proposals.md  # 改进方案
│   ├── skill_development_guide.md # 技能开发指南
│   └── api_reference.md     # API 接口文档
├── skills/                  # 技能实现目录
│   ├── poi/                 # POI 搜索类技能
│   ├── geocode/             # 地理编码类技能
│   ├── route/               # 路径规划类技能
│   ├── map/                 # 地图交互类技能
│   └── industry/            # 行业场景类技能
├── core/                    # 核心框架
│   ├── base_skill.py        # 技能基类
│   ├── skill_registry.py    # 技能注册器
│   └── skill_invoker.py     # 技能调用器
└── README.md                # 说明文档
```

## 技能开发规范

### 1. 技能定义
每个技能需要继承 `BaseSkill` 基类，并实现以下方法：
```python
from amap_skill.core.base_skill import BaseSkill

class MySkill(BaseSkill):
    name = "my_skill"  # 技能唯一标识
    description = "技能描述"  # 技能功能说明
    parameters = [     # 技能参数定义
        {
            "name": "param1",
            "type": "string",
            "description": "参数描述",
            "required": True
        }
    ]
    
    async def execute(self, **kwargs):
        # 技能具体实现逻辑
        pass
```

### 2. 技能注册
在技能实现文件中添加自动注册逻辑：
```python
from amap_skill.core.skill_registry import register_skill

@register_skill
class MySkill(BaseSkill):
    # 技能实现
    pass
```

### 3. 技能调用
技能注册后会自动暴露为 MCP 工具，可直接通过智能体调用：
```python
# 方式1：直接调用
result = await skill_invoker.invoke("my_skill", param1="value")

# 方式2：通过 MCP 调用
from amap_mcp.server import mcp
result = await mcp.call_tool("my_skill", {"param1": "value"})
```

## 现有技能列表

| 技能名称 | 功能描述 | 状态 |
|---------|---------|------|
| `geocode` | 地址转坐标 | ✅ 已实现 |
| `reverse_geocode` | 坐标转地址 | ✅ 已实现 |
| `route_planning` | 路径规划（步行/驾车/骑行） | ✅ 已实现 |
| `distance_measure` | 距离量算 | ✅ 已实现 |
| `poi_keyword_search` | 关键词 POI 搜索 | ⏳ 待实现 |
| `poi_around_search` | 周边 POI 搜索 | ⏳ 待实现 |
| `public_transit_planning` | 公交路径规划 | ⏳ 待实现 |
| `district_search` | 行政区域查询 | ⏳ 待实现 |
| `weather_search` | 天气查询 | ⏳ 待实现 |

## 集成到现有系统

### 1. 后端集成
在 `amap_mcp/server.py` 中添加技能自动加载逻辑：
```python
from amap_skill.core.skill_registry import load_all_skills

# 加载所有技能
skills = load_all_skills()
for skill in skills:
    # 注册为 MCP 工具
    mcp.tool()(skill.execute)
```

### 2. 前端集成
在 `web/src/components/MapContainer.vue` 中添加前端技能挂载点：
```javascript
import { loadMapSkills } from '@/amap_skill/map_skills'

// 地图加载完成后初始化前端技能
loadMapSkills(map.value)
```

### 3. 智能体配置
在 `.opencode/agents/` 中添加对应技能的智能体配置，例如：
```markdown
# poi-searcher.md
## 功能
专门处理 POI 搜索相关问题，支持关键词搜索、周边搜索、详情查询等。

## 工具
仅使用 `poi_keyword_search`、`poi_around_search`、`poi_detail_search` 工具。
```

## 贡献指南

1. 在对应类别目录下创建技能实现文件
2. 遵循技能开发规范实现功能
3. 添加对应的单元测试
4. 更新文档和技能列表
