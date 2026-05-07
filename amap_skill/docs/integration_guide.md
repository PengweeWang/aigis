# 系统集成指南

本文档介绍如何将 Amap Skill 框架集成到现有系统中。

## 一、后端集成

### 步骤1：更新依赖
确保 `requirements.txt` 包含以下依赖（已有可忽略）：
```
httpx>=0.24.0
mcp>=0.1.0
fastmcp>=0.1.0
```

### 步骤2：修改 amap_mcp/server.py
在 `amap_mcp/server.py` 中添加技能加载逻辑：

```python
# 在文件头部添加导入
from amap_skill import load_all_skills

# 在 mcp = FastMCP("amap-gis-mcp") 之后添加：
# 自动加载所有自定义技能
skills = load_all_skills()
for skill in skills:
    # 动态注册为 MCP 工具
    mcp.tool(name=skill.name, description=skill.description)(skill.execute)
```

### 步骤3：更新 opencode.json
在 `opencode.json` 的 `tools` 数组中添加新技能的引用（可选，自动加载可不需要）：
```json
{
  "tools": [
    {
      "name": "poi_keyword_search",
      "description": "根据关键词搜索POI兴趣点，支持按城市和类型筛选",
      "parameters": {
        "type": "object",
        "properties": {
          "keywords": {
            "type": "string",
            "description": "搜索关键词，多个关键词用|分隔"
          },
          "city": {
            "type": "string",
            "description": "城市名、拼音、citycode或adcode，可选"
          }
        },
        "required": ["keywords"]
      }
    }
  ]
}
```

### 步骤4：添加智能体配置
在 `.opencode/agents/` 目录下添加对应智能体配置文件，例如 `poi-searcher.md`：
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
- poi_around_search (待实现)
- poi_detail_search (待实现)

## 规则
1. 当用户询问地点相关问题时，优先使用POI搜索工具
2. 返回多个结果时，最多展示前5条最相关的结果
3. 位置坐标自动在地图上标注显示
4. 当用户需要查看更多结果时，支持分页查询
```

### 步骤5：更新主调度器
在 `.opencode/agents/gis-orchestrator.md` 中添加对新技能的调度规则：
```markdown
## 调度规则
1. 地理编码相关问题 → 委派给 geocoder 智能体
2. 距离计算相关问题 → 委派给 distance-measure 智能体
3. 路径规划相关问题 → 委派给 route-planner 智能体
4. POI搜索相关问题 → 委派给 poi-searcher 智能体
5. 行政区域查询相关问题 → 委派给 district-queryer 智能体 (待实现)
6. 天气查询相关问题 → 委派给 weather-assistant 智能体 (待实现)
```

## 二、前端集成

### 步骤1：创建前端技能目录
在 `web/src/` 目录下创建 `amap_skill/` 目录结构：
```
web/src/amap_skill/
├── skills/           # 前端技能实现
│   ├── map_annotation.js
│   ├── route_render.js
│   └── poi_display.js
├── core/             # 前端核心框架
│   ├── base_skill.js
│   └── skill_manager.js
└── index.js          # 导出接口
```

### 步骤2：实现前端技能基类
`web/src/amap_skill/core/base_skill.js`:
```javascript
export class BaseMapSkill {
  constructor(map) {
    this.map = map
  }
  
  // 技能初始化
  init() {
    // 子类实现
  }
  
  // 技能销毁
  destroy() {
    // 子类实现
  }
}
```

### 步骤3：实现技能管理器
`web/src/amap_skill/core/skill_manager.js`:
```javascript
export class SkillManager {
  constructor(map) {
    this.map = map
    this.skills = {}
  }
  
  register(skillName, SkillClass) {
    this.skills[skillName] = new SkillClass(this.map)
    return this.skills[skillName]
  }
  
  get(skillName) {
    return this.skills[skillName]
  }
  
  invoke(skillName, method, ...args) {
    const skill = this.get(skillName)
    if (skill && typeof skill[method] === 'function') {
      return skill[method](...args)
    }
    throw new Error(`技能 ${skillName} 不存在或方法 ${method} 未实现`)
  }
}
```

### 步骤4：修改 MapContainer.vue
在 `web/src/components/MapContainer.vue` 中集成技能管理器：
```javascript
<script setup>
import { onMounted, ref } from 'vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import { SkillManager } from '@/amap_skill/core/skill_manager'
import { MapAnnotationSkill } from '@/amap_skill/skills/map_annotation'
import { RouteRenderSkill } from '@/amap_skill/skills/route_render'

const map = ref(null)
const skillManager = ref(null)

onMounted(() => {
  window._AMapSecurityConfig = {
    securityJsCode: import.meta.env.VITE_AMAP_SECURITY_CODE,
  };

  AMapLoader.load({
    key: import.meta.env.VITE_AMAP_KEY,
    version: '2.0',
    plugins: ['AMap.Scale', 'AMap.ToolBar'],
  }).then((AMap) => {
    map.value = new AMap.Map('map-container', {
      viewMode: '2D',
      zoom: 11,
      center: [116.39, 39.90],
    });

    // 初始化技能管理器
    skillManager.value = new SkillManager(map.value)
    
    // 注册前端技能
    skillManager.value.register('annotation', MapAnnotationSkill)
    skillManager.value.register('routeRender', RouteRenderSkill)

    // 现有控件添加
    map.value.addControl(new AMap.Scale());
    map.value.addControl(new AMap.ToolBar({ position: 'RT' }));
  });
});

// 暴露技能管理器给父组件
defineExpose({
  // 现有方法...
  skillManager: skillManager.value
});
</script>
```

### 步骤5：修改 ChatPanel.vue
在 `web/src/components/ChatPanel.vue` 中添加技能调用逻辑：
```javascript
// 处理智能体返回的结果
const handleAgentResponse = async (response) => {
  // 现有处理逻辑...
  
  // 如果返回结果包含 POI 数据，自动调用前端技能标注
  if (response.data && response.data.pois) {
    const mapContainer = mapRef.value
    if (mapContainer && mapContainer.skillManager) {
      mapContainer.skillManager.invoke(
        'annotation', 
        'addPoiMarkers', 
        response.data.pois
      )
    }
  }
  
  // 如果返回结果包含路径数据，自动调用前端技能渲染路线
  if (response.data && response.data.route_polyline) {
    const mapContainer = mapRef.value
    if (mapContainer && mapContainer.skillManager) {
      mapContainer.skillManager.invoke(
        'routeRender', 
        'renderRoute', 
        response.data.route_polyline,
        {
          mode: response.data.mode,
          distance: response.data.distance_m,
          duration: response.data.duration_s
        }
      )
    }
  }
}
```

## 三、测试集成效果

### 1. 启动后端服务
```bash
python -m amap_mcp.server
```
检查控制台输出，确认技能已成功加载：
```
Loaded skills:
- geocode
- reverse_geocode
- route_planning
- distance_measure
- poi_keyword_search
```

### 2. 启动前端服务
```bash
cd web && npm run dev
```
访问 http://localhost:8080，确认地图正常加载。

### 3. 测试技能调用
在对话面板输入："帮我搜索北京的咖啡店"
预期结果：
- 智能体调用 `poi_keyword_search` 工具
- 返回咖啡店列表
- 前端自动在地图上标注这些咖啡店的位置
- 点击标注可以查看详情

## 四、部署注意事项

### 1. 环境变量
确保生产环境配置了正确的高德 API Key：
```bash
AMAP_API_KEY=your_api_key_here
VITE_AMAP_KEY=your_web_api_key_here
VITE_AMAP_SECURITY_CODE=your_security_code_here
```

### 2. API 配额
高德 API 有调用次数限制，建议：
- 开启技能调用缓存，减少重复请求
- 配置限流机制，防止超出配额
- 监控 API 调用情况，及时调整配额

### 3. 性能优化
- 大结果集分页返回，避免一次返回过多数据
- 前端使用懒加载，提升地图渲染性能
- 静态资源使用 CDN 加速

### 4. 错误处理
- 添加 API 调用失败重试机制
- 网络异常时给出友好提示
- 记录错误日志，便于问题排查

## 五、扩展开发

### 添加新技能的完整流程
1. 在 `amap_skill/skills/` 对应目录下实现后端技能
2. 编写前端展示逻辑（如果需要）
3. 添加对应的智能体配置
4. 更新调度器规则
5. 编写单元测试和集成测试
6. 更新文档

### 常见问题排查
1. **技能没有被加载**：检查技能文件是否放在正确的目录，是否使用了 `@register_skill` 装饰器
2. **MCP 调用失败**：检查参数是否符合定义，后端服务是否正常运行
3. **前端技能不工作**：检查地图是否已加载完成，技能是否正确注册
4. **高德 API 返回错误**：检查 API Key 是否正确，参数是否符合高德 API 文档要求
