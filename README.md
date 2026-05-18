# AIGIS

**AI + GIS** — 基于大语言模型 Agent 的地理信息系统智能助手。

用户通过自然语言聊天界面与 GIS 系统交互，可进行地点查询、距离量算、路径规划等操作，结果实时展示在交互式地图上。

## 架构

```
用户浏览器 (Vue 3 + AMap 地图)
       │
       │  WebSocket (ws://localhost:8000/ws/data)
       ▼
┌─────────────────────────────────┐
│  FastAPI 数据中继服务器         │  ← port 8000
│  (server/app.py)                │
│  - REST: /api/set, /api/final   │
│  - WS:   /ws/data               │
└──────────┬──────────────────────┘
           │ HTTP
           ▼
┌─────────────────────────────────┐
│  MCP 服务器 (mcps/server.py)    │  ← GIS 工具层
│  - geocode / geodecode          │
│  - route_planning               │
│  - direction_distence           │
│  - set_final                    │
│  ┌─────────────────────────┐    │
│  │  api/amap.py(高德 API)  │    │
│  │  api/utils.py(Haversine)│    │
│  └─────────────────────────┘    │
└──────────┬──────────────────────┘
           │ MCP 协议
           ▼
┌─────────────────────────────────┐
│  OpenCode 平台                  │  ← port 4096
│  (opencode serve)               │
│  - gis-orchestrator 编排 Agent  │
│    ├─ geocoder 子 Agent         │
│    ├─ distance-measure 子 Agent │
│    └─ route-planner 子 Agent    │
└─────────────────────────────────┘
           │ HTTP 代理 (Vite)
           ▼
┌─────────────────────────────────┐
│  Vue 3 前端                     │  ← port 8080
│  - ChatPanel (AI 聊天界面)      │
│  - MapContainer (AMap 地图)     │
└─────────────────────────────────┘
```

## 技术栈

| 层 | 技术 |
|---|---|
| MCP 服务器 | Python 3, FastMCP |
| 数据服务器 | Python 3, FastAPI, Uvicorn, WebSocket |
| GIS 客户端 | Python 3, requests (高德地图 API) |
| 前端 | Vue 3 (Composition API), Vite 5 |
| 地图 | @amap/amap-jsapi-loader v1.0 (AMap JSAPI v2.0) |
| AI 聊天 UI | element-ai-vue v0.1.6 |
| AI Agent | OpenCode + MCP 协议 |

## 快速开始

### 前置条件

- Python 3.10+
- Node.js 18+
- OpenCode CLI

### 配置

复制环境变量文件并填写密钥：

```bash
cp .env.example .env
# 编辑 .env，填入 AMAP_API_KEY
cp web/.env.example web/.env
# 编辑 web/.env，填入 VITE_AMAP_KEY 和 VITE_AMAP_SECURITY_CODE
```

### 启动

一键启动所有服务：

```bash
bash start.sh
```

或分别启动：

```bash
# 1. 数据中继服务器
uvicorn server.app:app --port 8000

# 2. MCP 服务器
python -m mcps.server

# 3. OpenCode 平台
opencode serve

# 4. 前端开发服务器
cd web && npm run dev
```

## 项目结构

```
├── api/              # GIS API 客户端库 (Python)
│   ├── amap.py       # 高德地图 API 封装
│   ├── dbrg.py       # DBRG 客户端 (预留)
│   └── utils.py      # Haversine 距离计算
├── mcps/             # MCP 服务器 (Python)
│   └── server.py     # GIS 工具暴露层
├── server/           # FastAPI 数据中继服务器
│   └── app.py        # REST + WebSocket 端点
├── web/              # Vue 3 前端
│   └── src/
│       ├── App.vue
│       └── components/
│           ├── ChatPanel.vue      # AI 聊天面板
│           └── MapContainer.vue   # AMap 地图容器
├── test/             # 测试
├── opencode.json     # OpenCode Agent 配置
└── start.sh          # 启动脚本
```

## 功能

- **地理编码/逆地理编码** — 地址 ↔ 坐标 双向查询，地图标注
- **路径规划** — 驾车/步行/骑行路线规划，路线绘制
- **距离量算** — 两点间直线距离计算（Haversine），虚线标注
- **实时推送** — WebSocket 将 GIS 数据实时推送到前端地图

## 环境变量

| 变量 | 说明 |
|---|---|
| `AMAP_API_KEY` | 高德地图服务端 API Key |
| `VITE_AMAP_KEY` | 高德地图 Web JSAPI Key |
| `VITE_AMAP_SECURITY_CODE` | 高德地图安全密钥 |
| `DATA_SERVER_URL` | 数据服务器地址 (默认 http://localhost:8000) |

## MCP、API、前端用户标注格式参照

[`api/README.md`](api/README.md)。 
[`server/README.md`](server/README.md)
[`web/README.md`](web/README.md)


## 许可

MIT
