# 技能开发指南

本文档介绍如何开发新的 Amap Skill 并集成到现有系统中。

## 一、开发前准备

### 1. 确认需求
- 明确技能要解决的问题和应用场景
- 确认对应的高德 API 接口是否支持
- 评估是否需要前端 JS API 配合

### 2. 查阅文档
- 高德 REST API 文档：https://lbs.amap.com/api/webservice/summary
- 高德 JS API 文档：https://lbs.amap.com/api/javascript-api-v2/summary
- 现有代码规范：参考 `amap_mcp/server.py` 中的实现

## 二、后端技能开发流程

### 步骤1：创建技能文件
在 `amap_skill/skills/` 对应的类别目录下创建新的技能文件，例如：
```bash
touch amap_skill/skills/poi/poi_keyword_search.py
```

### 步骤2：实现技能逻辑
```python
from typing import Optional, Dict, Any
import json
from amap_skill.core.base_skill import BaseSkill
from amap_skill.core.skill_registry import register_skill
from amap_mcp.server import amap_get

@register_skill
class PoiKeywordSearchSkill(BaseSkill):
    name = "poi_keyword_search"
    description = "根据关键词搜索POI兴趣点，支持按城市筛选"
    parameters = [
        {
            "name": "keywords",
            "type": "string",
            "description": "搜索关键词，多个用|分隔",
            "required": True
        },
        {
            "name": "city",
            "type": "string",
            "description": "城市名/拼音/citycode/adcode，可选",
            "required": False
        },
        {
            "name": "types",
            "type": "string",
            "description": "POI类型，多个用|分隔，可选",
            "required": False
        },
        {
            "name": "page_size",
            "type": "integer",
            "description": "每页结果数量，默认20，最大50",
            "required": False
        },
        {
            "name": "page_num",
            "type": "integer",
            "description": "页码，默认1",
            "required": False
        }
    ]
    
    async def execute(
        self,
        keywords: str,
        city: Optional[str] = None,
        types: Optional[str] = None,
        page_size: int = 20,
        page_num: int = 1
    ) -> str:
        """
        执行POI关键词搜索
        """
        params: Dict[str, Any] = {
            "keywords": keywords,
            "output": "JSON",
            "page_size": max(1, min(page_size, 50)),
            "page_num": max(1, page_num)
        }
        
        if city:
            params["city"] = city
            params["citylimit"] = True  # 仅返回指定城市结果
            
        if types:
            params["types"] = types
            
        data = await amap_get("/v3/place/text", params)
        
        # 精简返回结果，避免返回过多无关字段
        pois = data.get("pois", [])
        simplified_pois = []
        for poi in pois[:20]:  # 最多返回20条结果
            simplified_pois.append({
                "id": poi.get("id"),
                "name": poi.get("name"),
                "type": poi.get("type"),
                "address": poi.get("address"),
                "location": poi.get("location"),
                "distance": poi.get("distance"),
                "tel": poi.get("tel")
            })
            
        result = {
            "count": data.get("count", 0),
            "pois": simplified_pois
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
```

### 步骤3：注册到 MCP 服务
在 `amap_mcp/server.py` 中添加技能加载逻辑：
```python
# 在文件头部导入
from amap_skill.core.skill_registry import load_all_skills

# 在 mcp = FastMCP("amap-gis-mcp") 之后添加
# 自动加载所有自定义技能
skills = load_all_skills()
for skill in skills:
    # 动态注册为 MCP 工具
    mcp.tool(name=skill.name, description=skill.description)(skill.execute)
```

### 步骤4：配置智能体
在 `.opencode/agents/poi-searcher.md` 中添加智能体配置：
```markdown
# POI 搜索智能体

## 功能
专门处理所有与POI搜索相关的问题，包括：
- 关键词搜索POI
- 周边搜索POI
- 查询POI详情
- 按类型搜索POI

## 工具
仅使用以下工具：
- poi_keyword_search
- poi_around_search
- poi_detail_search

## 规则
1. 当用户询问地点相关问题时，优先使用POI搜索工具
2. 返回多个结果时，最多展示前5条最相关的结果
3. 当用户需要查看更多结果时，支持分页查询
4. 位置坐标自动在地图上标注显示
```

## 三、前端技能开发流程

### 步骤1：创建前端技能文件
在 `web/src/amap_skill/skills/` 目录下创建技能文件：
```bash
touch web/src/amap_skill/skills/map_annotation.js
```

### 步骤2：实现前端技能
```javascript
/**
 * 地图标注技能
 * 支持在地图上添加各种类型的标注
 */
export class MapAnnotationSkill {
  constructor(map) {
    this.map = map
    this.markers = []
  }
  
  /**
   * 添加POI标注
   * @param {Array} poiList POI列表
   * @param {Object} options 配置选项
   */
  addPoiMarkers(poiList, options = {}) {
    poiList.forEach(poi => {
      if (!poi.location) return
      
      const [lng, lat] = poi.location.split(',').map(Number)
      
      const marker = new AMap.Marker({
        position: [lng, lat],
        title: poi.name,
        icon: options.icon || this.getDefaultIcon(poi.type),
        label: {
          content: poi.name,
          direction: 'bottom',
          offset: new AMap.Pixel(0, 10)
        },
        ...options
      })
      
      // 添加点击事件，显示详情
      marker.on('click', () => {
        this.showPoiInfo(poi)
      })
      
      this.map.add(marker)
      this.markers.push(marker)
    })
  }
  
  /**
   * 根据POI类型获取默认图标
   */
  getDefaultIcon(type) {
    const iconMap = {
      '餐饮': '//a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-restaurant.png',
      '酒店': '//a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-hotel.png',
      '购物': '//a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-shopping.png',
      '医疗': '//a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-hospital.png',
      '交通': '//a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-bus.png'
    }
    
    for (const key in iconMap) {
      if (type && type.includes(key)) {
        return iconMap[key]
      }
    }
    
    return '//a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-default.png'
  }
  
  /**
   * 显示POI详情弹窗
   */
  showPoiInfo(poi) {
    const infoWindow = new AMap.InfoWindow({
      anchor: 'bottom-center',
      content: `
        <div style="padding: 10px; min-width: 200px;">
          <h3 style="margin: 0 0 8px 0;">${poi.name}</h3>
          <p style="margin: 4px 0; color: #666;">${poi.address || '地址不详'}</p>
          ${poi.tel ? `<p style="margin: 4px 0; color: #666;">电话：${poi.tel}</p>` : ''}
          ${poi.distance ? `<p style="margin: 4px 0; color: #666;">距离：${poi.distance}米</p>` : ''}
        </div>
      `,
      offset: new AMap.Pixel(0, -30)
    })
    
    const [lng, lat] = poi.location.split(',').map(Number)
    infoWindow.open(this.map, [lng, lat])
  }
  
  /**
   * 清除所有标注
   */
  clear() {
    this.map.remove(this.markers)
    this.markers = []
  }
}
```

### 步骤3：注册前端技能
在 `web/src/components/MapContainer.vue` 中注册技能：
```javascript
import { MapAnnotationSkill } from '@/amap_skill/skills/map_annotation'

// 在地图加载完成后
const mapSkills = ref({})

// 在 AMapLoader.load().then() 回调中
mapSkills.value.annotation = new MapAnnotationSkill(map.value)

// 暴露给父组件
defineExpose({
  // ... 现有方法
  ...mapSkills.value
})
```

## 四、测试与发布

### 1. 单元测试
为每个技能编写单元测试，测试用例包括：
- 正常参数调用
- 边界参数测试
- 错误参数处理
- API 异常处理

### 2. 集成测试
测试技能的全流程调用：
- 前端用户提问
- 智能体调用技能
- 后端 API 调用
- 结果返回和前端展示

### 3. 性能优化
- 对于高频调用的技能添加缓存机制
- 大结果集进行分页处理
- 异步非阻塞调用

### 4. 文档更新
- 更新 `improvement_proposals.md` 中的技能状态
- 更新 `README.md` 中的技能列表
- 添加技能使用示例和最佳实践

## 五、最佳实践

### 1. 参数设计
- 必选参数放在前面，可选参数放在后面
- 参数提供合理的默认值
- 对参数进行合法性校验，避免无效 API 调用

### 2. 返回结果
- 精简返回字段，只返回必要的信息
- 统一返回格式，便于前端处理
- 错误信息友好，便于问题排查

### 3. 安全考虑
- 避免返回敏感信息
- 对用户输入进行合法性校验，防止注入攻击
- API 调用添加限流和熔断机制

### 4. 用户体验
- 复杂问题分步骤处理，及时反馈进度
- 结果展示简洁明了，重点信息突出
- 支持多轮交互，处理用户的后续追问
