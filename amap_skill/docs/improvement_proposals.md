# 高德地图 API 技能改进方案

基于高德地图 JS API v2 的 Skill 能力设计，结合现有代码实现，提出以下可扩展的技能改进方案，所有新增技能可统一在 `amap_skill/skills/` 目录下管理。

---

## 一、POI 搜索类技能

### 1. 关键词搜索技能 (`poi_keyword_search`) ✅ 已实现
**功能描述**：根据关键词搜索周边/指定城市的 POI 兴趣点
**集成方式**：调用高德 `/v3/place/text` REST API
**实现文件**：`amap_skill/skills/poi/poi_keyword_search.py`
**参数设计**：
```python
async def poi_keyword_search(
    keywords: str,
    city: Optional[str] = None,
    types: Optional[str] = None,
    page_size: int = 20,
    page_num: int = 1
) -> str:
```
**应用场景**：用户问"找附近的咖啡店"、"北京有哪些三甲医院"等

### 2. 周边搜索技能 (`poi_around_search`) ✅ 已实现
**功能描述**：根据中心点坐标搜索周边特定类型的 POI
**集成方式**：调用高德 `/v3/place/around` REST API
**实现文件**：`amap_skill/skills/poi/poi_around_search.py`
**参数设计**：
```python
async def poi_around_search(
    location: str,
    radius: int = 3000,
    keywords: Optional[str] = None,
    types: Optional[str] = None,
    page_size: int = 20,
    page_num: int = 1
) -> str:
```
**应用场景**：用户问"我现在位置附近1公里内的停车场"等

### 3. POI 详情查询技能 (`poi_detail_search`) ✅ 已实现
**功能描述**：根据 POI ID 查询详细信息（电话、营业时间、评分等）
**集成方式**：调用高德 `/v3/place/detail` REST API
**实现文件**：`amap_skill/skills/poi/poi_detail_search.py`
**参数设计**：
```python
async def poi_detail_search(poi_id: str) -> str:
```
**应用场景**：用户问"这个商场的营业时间是多少"等

---

## 二、地理编码增强类技能

### 4. 批量地理编码技能 (`batch_geocode`) ✅ 已实现
**功能描述**：同时转换多个地址为坐标，一次最多处理10个地址
**集成方式**：批量调用 `geocode` 接口
**实现文件**：`amap_skill/skills/geocode/batch_geocode.py`
**参数设计**：
```python
async def batch_geocode(addresses: List[str], city: Optional[str] = None) -> str:
```
**应用场景**：用户需要将多个地址批量转换为坐标进行展示

### 5. 地址标准化技能 (`address_standardize`) ⏳ 待实现
**功能描述**：将非结构化地址解析为标准化的省市区街道结构
**集成方式**：基于地理编码返回结果增强处理
**参数设计**：
```python
async def address_standardize(address: str) -> str:
```
**应用场景**：用户输入不规范地址时自动结构化处理

---

## 三、路径规划增强类技能

### 6. 公交路径规划技能 (`public_transit_planning`) ✅ 已实现
**功能描述**：支持公交、地铁等公共交通路径规划
**集成方式**：调用高德 `/v3/direction/transit/integrated` REST API
**实现文件**：`amap_skill/skills/route/public_transit_planning.py`
**参数设计**：
```python
async def public_transit_planning(
    origin: str,
    destination: str,
    city: str,
    cityd: Optional[str] = None,
    strategy: int = 0,
    nightflag: int = 0
) -> str:
```
**应用场景**：用户问"从国贸到中关村坐地铁怎么走"等

### 7. 货车路径规划技能 (`truck_planning`) ✅ 已实现
**功能描述**：针对货车的限行规则进行路径规划，支持设置车辆参数
**集成方式**：调用高德 `/v4/direction/truck` REST API
**实现文件**：`amap_skill/skills/route/truck_planning.py`
**参数设计**：
```python
async def truck_planning(
    origin: str,
    destination: str,
    truck_type: int = 2,
    weight: float = 1.5,
    height: float = 3.5,
    width: float = 2.5,
    load_weight: float = 10,
    axis: int = 2,
    strategy: int = 0
) -> str:
```
**应用场景**：货车司机规划运输路线，避开限行区域

### 8. 骑行/步行导航增强技能 (`navigation_enhance`) ⏳ 待实现
**功能描述**：提供实时导航语音提示、路口放大图等增强功能
**集成方式**：结合前端 JS API 的导航组件实现
**参数设计**：
```python
async def navigation_enhance(
    route_id: str,
    current_location: str,
    mode: str = "walking"
) -> str:
```
**应用场景**：用户进行实时导航时的引导提示

---

## 四、地图交互类技能

### 9. 行政区域查询技能 (`district_search`) ✅ 已实现
**功能描述**：查询行政区域边界、编码、下级区域等信息
**集成方式**：调用高德 `/v3/config/district` REST API
**实现文件**：`amap_skill/skills/map/district_search.py`
**参数设计**：
```python
async def district_search(
    keywords: str,
    subdistrict: int = 1,
    extensions: str = "base"
) -> str:
```
**应用场景**：用户问"上海市有哪些区"、"画出北京市的边界"等

### 10. 天气查询技能 (`weather_search`) ✅ 已实现
**功能描述**：查询指定城市的实时天气和预报
**集成方式**：调用高德 `/v3/weather/weatherInfo` REST API
**实现文件**：`amap_skill/skills/map/weather_search.py`
**参数设计**：
```python
async def weather_search(
    city: str,
    extensions: str = "base"
) -> str:
```
**应用场景**：用户问"北京明天天气怎么样"、"上海今天会下雨吗"等

### 11. 坐标转换技能 (`coordinate_convert`) ✅ 已实现
**功能描述**：支持不同坐标系之间的转换（GPS、百度、Mapbar等）
**集成方式**：调用高德 `/v3/assistant/coordinate/convert` REST API
**实现文件**：`amap_skill/skills/map/coordinate_convert.py`
**参数设计**：
```python
async def coordinate_convert(
    locations: str,
    coordsys: str = "gps"
) -> str:
```
**应用场景**：处理第三方设备坐标数据在高德地图上的展示

### 12. 静态地图技能 (`static_map`) ✅ 已实现
**功能描述**：生成静态地图图片URL，支持标注点、路线等叠加
**集成方式**：调用高德 `/v3/staticmap` REST API
**实现文件**：`amap_skill/skills/map/static_map.py`
**参数设计**：
```python
async def static_map(
    location: str,
    zoom: int = 11,
    size: str = "400*300",
    markers: str = "",
    paths: str = ""
) -> str:
```
**应用场景**：在聊天中直接展示地图缩略图

---

## 五、行业场景类技能

### 13. 物流路径规划技能 (`logistics_planning`) ✅ 已实现
**功能描述**：支持多途径点的物流配送路径优化，自动优化途径点顺序
**集成方式**：调用高德 `/v3/direction/driving` 结合途径点优化
**实现文件**：`amap_skill/skills/industry/logistics_planning.py`
**参数设计**：
```python
async def logistics_planning(
    origin: str,
    destination: str,
    waypoints: List[str],
    optimize_order: bool = True,
    strategy: int = 0
) -> str:
```
**应用场景**：快递配送、货运调度等场景的路径优化

### 14. IP 定位技能 (`ip_location`) ✅ 已实现
**功能描述**：根据IP地址查询地理位置信息
**集成方式**：调用高德 `/v3/ip` REST API
**实现文件**：`amap_skill/skills/industry/ip_location.py`
**参数设计**：
```python
async def ip_location(ip: str = "") -> str:
```
**应用场景**：根据用户IP粗略定位所在城市

### 15. 地理围栏技能 (`geofence`) ⏳ 待实现
**功能描述**：创建、管理地理围栏，实现进出围栏的事件触发
**集成方式**：结合前端 JS API 的 GeoFence 组件实现
**参数设计**：
```python
async def geofence_create(
    name: str,
    center: str,
    radius: int,
    alert_type: str = "enter|leave"
) -> str:
```
**应用场景**：考勤打卡、区域告警、资产监控等场景

---

## 六、前端增强技能（JS API Skill 集成）

### 16. 地图标注技能 (`map_annotation`) ⏳ 待实现
**功能描述**：支持在地图上添加自定义标注、文本、图形等
**集成方式**：封装前端 JS API 的 Marker、Text、Polygon 等类
**参数设计**：
```typescript
function addAnnotation(
    type: 'marker' | 'text' | 'polygon' | 'circle',
    options: any
): void
```

### 17. 路线实时渲染技能 (`route_render`) ⏳ 待实现
**功能描述**：动态渲染规划路线、实时轨迹、拥堵路段等
**集成方式**：封装前端 JS API 的 Polyline、PolylineEditor 等类
**参数设计**：
```typescript
function renderRoute(
    path: Array<[number, number]>,
    color: string = '#3366FF',
    width: number = 6,
    showTraffic: boolean = false
): void
```

---

## 架构改进建议

### 1. 技能模块化管理 ✅ 已实现
- 在 `amap_skill/skills/` 下按类别创建子目录：`poi/`、`geocode/`、`route/`、`map/`、`industry/`
- 每个技能独立实现，通过统一的 `BaseSkill` 基类对外暴露接口
- 新增技能通过 `@register_skill` 装饰器自动注册，无需手动修改 `opencode.json`
- `SkillRegistry` 管理所有技能的注册与查找

### 2. 前后端技能协同 ⏳ 待实现
- 后端 MCP 技能负责数据获取和业务逻辑处理
- 前端 JS API Skill 负责地图交互和可视化展示
- 通过标准化的事件总线实现前后端技能的联动调用

### 3. 技能调用优化 ✅ 已实现
- `SkillInvoker` 实现技能调用缓存机制，减少重复 API 请求
- 添加限流机制（默认每分钟100次），保护高德 API 调用配额
- 参数校验和类型检查

### 4. 智能体技能适配 ✅ 已实现
- 新增智能体：`poi-searcher`、`district-queryer`、`weather-assistant`、`transit-planner`
- 主调度器已更新调度规则，支持7个子智能体
- 支持多技能组合调用，实现复杂场景的自动化处理
