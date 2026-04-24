# AMap GIS

基于高德地图 API 的 opencode 智能体项目，提供地名查询、距离量算、路径规划等 GIS 功能。

## 智能体

| 智能体 | 说明 |
|--------|------|
| `gis-orchestrator` | 主调度智能体，负责分发任务到子智能体 |
| `geocoder` | 地名地址查询（地理编码/逆地理编码） |
| `distance-measure` | 距离量算（驾车/步行） |
| `route-planner` | 路径规划（驾车/步行/公交） |

## 使用方式

在 opencode 中直接描述需求，例如：
- "从天安门到故宫怎么走？"
- "北京市朝阳区阜通东大街6号在哪里？"
- "计算望京到中关村的驾车距离"

主调度智能体会自动识别问题类型并调用相应的子智能体处理。

## 开发

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置 API Key
```bash
cp .env.example .env
AMAP_API_KEY=your_key
```

## Acknowledgement

感谢国防科技大学电子科学学院对本项目的资助。
