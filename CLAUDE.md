# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览
基于高德地图 API 的 opencode 智能体项目，提供地名查询、距离量算、路径规划等 GIS 功能，通过 MCP 服务暴露工具供多智能体调度系统调用。前端为 Vue 3 + 高德地图 JS API 的对话式交互界面。

## 数据流
```
用户 → ChatPanel (web:8080) → opencode serve (:4096)
  → gis-orchestrator（主调度，禁用所有工具，纯委派）
    ├→ geocoder → geocode / reverse_geocode
    ├→ distance-measure → distance_measure
    └→ route-planner → route_planning（内部可能再委派 geocoder 获取坐标）
      → amap_mcp/server.py (MCP 工具)
        → 高德 REST API (restapi.amap.com)
```

## 架构说明

### MCP 服务（`amap_mcp/server.py`）
基于 FastMCP 框架，暴露 4 个 `@mcp.tool()` 异步函数：

| 工具 | 功能 | 高德 API |
|------|------|----------|
| `geocode` | 地址 → 坐标 | `/v3/geocode/geo` |
| `reverse_geocode` | 坐标 → 地址（可返回周边 POI/道路） | `/v3/geocode/regeo` |
| `route_planning` | 路径规划（步行/驾车/骑行） | `/v3/direction/{walking,driving,bicycling}` |
| `distance_measure` | 距离量算（驾车/步行） | 同 route_planning，仅返回距离和耗时 |

- 所有工具返回 JSON，通过 `amap_get()` 统一调高德 REST API
- 折线解析：`_parse_polyline()` 解码高德折线字符串为坐标列表
- 步骤精简：`_compact_walk_steps()` / `_compact_drive_steps()`

### 智能体体系（`.opencode/agents/`）
- **gis-orchestrator**（primary）：纯调度，所有工具禁用，按用户需求分发给子智能体
- **geocoder**：仅用 `geocode` + `reverse_geocode`，**地理编码返回多个候选时必须让用户确认，不能直接取第一个**（技能 `geocode-candidates-check` 强制执行此规则）
- **distance-measure**：仅用 `distance_measure`
- **route-planner**：用 `route_planning`，可委派 geocoder 获取起终点坐标

### Web 前端（`web/`）
Vue 3 + Vite 5 + element-ai-vue + @amap/amap-jsapi-loader

- **MapContainer.vue**：加载高德地图 JS API 2.0，默认北京 [116.39, 39.90]，提供 `addMarker` / `addPolyline` / `setCenter` / `clearMarkers` / `clearPolylines` 给子组件
- **ChatPanel.vue**：对话面板，通过 REST 与 opencode serve 通信（`/session`、`/session/{id}/message`），支持思维过程折叠展示和 Markdown 渲染
- **App.vue**：提供 `mapContainer` 上下文，桥接地图操作与对话
- Vite 代理：`/global`、`/session`、`/config`、`/provider` → `http://127.0.0.1:4096`

## 常用命令

### 环境配置
```bash
pip install -r requirements.txt          # Python 依赖（httpx, mcp）
cp .env.example .env                     # 填写 AMAP_API_KEY
cd web && npm install                    # 前端依赖
```

Web 前端额外需要配置 `web/.env`：
```
VITE_AMAP_KEY=你的高德Web端JS API密钥
VITE_AMAP_SECURITY_CODE=你的安全密钥
```

### 运行服务
```bash
# 一键启动（opencode serve + 前端 dev server）
bash start.sh

# 或分别启动
# 后端：opencode 自动根据 opencode.json 启动 MCP 服务
python -m amap_mcp.server               # 手动测试 MCP 服务
# 前端：
cd web && npm run dev                    # http://localhost:8080
```

### 前端构建
```bash
cd web && npm run build                  # 生产构建
cd web && npm run preview                # 预览生产构建
```

### 开发说明
- 新增/修改 MCP 工具：在 `amap_mcp/server.py` 中添加 `@mcp.tool()` 异步函数，然后在 `opencode.json` 的 `tools` 中注册
- 新增/修改智能体：在 `.opencode/agents/` 中添加 Markdown 文件，在 `opencode.json` 的 `agents` 中注册
- 环境变量加载：`_load_env_file()` 自动从 CWD、项目根目录、含 `opencode.json` 的父目录查找 `.env`
