# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AIGIS（AMap GIS）是基于高德地图 API 的智能 GIS 助手，采用多智能体架构，提供地名查询、距离量算、路径规划等功能。包含 Python MCP 服务端和 Vue 3 Web 前端两部分。

## 开发命令

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd web && npm install

# 启动开发环境（同时启动 opencode serve :4096 和 vite dev :8080）
bash start.sh

# 前端单独开发
cd web && npm run dev

# 前端构建
cd web && npm run build

# 运行 MCP 服务
python -m amap_mcp.server
```

## 环境配置

在项目根目录创建 `.env` 文件，设置 `AMAP_API_KEY=yourkey`。MCP 服务启动时会自动从 `.env` 加载密钥。

## 架构

```
用户 → Web 前端 (Vite + Vue 3, :8080)
         ↓ (API proxy → :4096)
       OpenCode Serve (:4096)
         ↓ (MCP protocol, stdio)
       amap_mcp/server.py (FastMCP)
         ↓ (HTTPS)
       高德地图 REST API
```

### 多智能体调度

`opencode.json` 定义了智能体层级，`gis-orchestrator` 为 primary agent，根据问题类型分发到子智能体：
- 地址查询 → `geocoder`（工具：`geocode`, `reverse_geocode`）
- 距离计算 → `distance-measure`（工具：`distance_measure`）
- 路径规划 → `route-planner`（工具：`route_planning`，可调用 `geocoder` 获取坐标）

智能体定义在 `.opencode/agents/`，技能定义在 `.opencode/skills/`。

### MCP 工具（amap_mcp/server.py）

四个工具注册在 FastMCP 上：
- `geocode(address, city?)` — 地理编码
- `reverse_geocode(location, radius?, extensions?)` — 逆地理编码
- `route_planning(origin, destination, mode?, strategy?, extensions?)` — 路径规划（walking/driving/cycling）
- `distance_measure(origin, destination, mode?)` — 距离量算（内部调用 `route_planning`）

### 前端组件

- `App.vue` — 根组件，通过 provide/inject 共享地图实例
- `MapContainer.vue` — 封装高德 JS API，暴露 `addMarker`/`addPolyline`/`setCenter`/`clearMarkers`/`clearPolylines` 方法
- `ChatPanel.vue` — 聊天面板，连接 OpenCode serve API（`/session`、`/session/{id}/message`、`/config/providers`）

### 前端代理

Vite 将 `/global`、`/session`、`/config`、`/provider` 路径代理到 `http://127.0.0.1:4096`（OpenCode serve）。

## 语言约定

项目面向中文用户，智能体 prompt 和 MCP 工具描述均为中文。修改智能体或工具时保持中文描述。
