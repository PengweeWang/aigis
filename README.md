# AMap GIS MCP + OpenCode GIS 智能体

这个项目实现了一个基于高德 WebService API 的 Python MCP Server，并提供 OpenCode GIS 智能体配置，支持：

- 地名地址查询（地理编码）
- 经纬度反查地址（逆地理编码）
- 距离量算（步行/驾车）
- 路径规划（步行/驾车/公交）

## 1. 文档要点（已按官方接口实现）

### 高德地理/逆地理编码

- 地理编码接口：`GET /v3/geocode/geo`
  - 必填：`key`、`address`
  - 可选：`city`
- 逆地理编码接口：`GET /v3/geocode/regeo`
  - 必填：`key`、`location`
  - 可选：`radius`、`extensions`

### 高德路径规划

- 步行：`GET /v3/direction/walking`
- 公交：`GET /v3/direction/transit/integrated`
- 驾车：`GET /v3/direction/driving`

说明：本项目的“距离量算”基于路径规划返回的路网距离（而非简单直线距离）。

### OpenCode agents / MCP-servers

- MCP 服务器通过 `opencode.json` 的 `mcp` 字段注册
- 本地 MCP 使用 `type: local` + `command`
- 可通过 `environment` 把环境变量传给 MCP 服务
- 可通过 `AMAP_DOTENV_PATH` 显式指定 `.env` 路径（如 `{workspaceRoot}/.env`）
- 可通过 agent 工具权限让 `gis-navigator` 仅使用 `amap_gis_*` 工具

## 2. 项目结构

- `amap_mcp/server.py`：MCP 服务主程序
- `amap_mcp/__init__.py`：包标识
- `requirements.txt`：Python 依赖
- `.env.example`：环境变量模板
- `opencode.json.example`：OpenCode MCP + agent 配置示例
- `.opencode/agents/gis-navigator.md`：GIS 子代理定义

## 3. 安装与配置

### 3.1 安装依赖

```bash
pip install -r requirements.txt
```

### 3.2 配置高德 Key

1. 在高德开放平台申请 Web 服务 API Key
2. 设置环境变量 `AMAP_API_KEY`（或在项目根目录 `.env` 中配置）

Linux/macOS:

```bash
export AMAP_API_KEY="你的高德Key"
```

Windows PowerShell:

```powershell
$env:AMAP_API_KEY="你的高德Key"
```

也可以在项目根目录创建 `.env`：

```dotenv
AMAP_API_KEY=你的高德Key
```

服务启动时会优先读取进程环境变量；若缺失则自动加载项目根目录 `.env`。

## 4. 启动 MCP Server

```bash
python -m amap_mcp.server
```

## 5. MCP 工具清单

服务名：`amap-gis-mcp`

- `geocode(address, city=None)`
  - 输入地址，返回候选坐标与地址要素
- `reverse_geocode(location, radius=1000, extensions="base")`
  - 输入经纬度，返回结构化地址（`extensions=all` 可返回周边 POI/道路）
- `route_planning(origin, destination, mode="driving", city=None, strategy=None, extensions="base")`
  - 支持 `driving` / `walking` / `transit`
  - `transit` 模式需要 `city`
- `distance_measure(origin, destination, mode="driving")`
  - 输出米/公里和秒/分钟

坐标格式统一为：`经度,纬度`（例如 `116.481028,39.989643`）。

## 6. 在 OpenCode 中接入

1. 复制 `opencode.json.example` 为你的 `opencode.json`（全局或项目级）
2. 确保系统环境变量中存在 `AMAP_API_KEY`，或项目根目录存在 `.env`
3. 启动 OpenCode 后，MCP 工具将以 `amap_gis_*` 前缀可用
4. 将 `.opencode/agents/gis-navigator.md` 放在项目目录下后，可通过 `@gis-navigator` 调用

示例提示词：

```text
@gis-navigator 帮我从北京西站到首都机场做驾车路线规划，并告诉我预计距离和时长
```

```text
@gis-navigator 把“上海市浦东新区张江高科技园区”转成经纬度
```

```text
@gis-navigator 我现在在 116.481028,39.989643，帮我查附近地址并给出步行到天安门的路线建议
```

## 7. 开发说明

- 环境变量与 `.env` 均缺失时会报错：`Environment variable AMAP_API_KEY is not set (and no AMAP_API_KEY found in .env)`
- 高德接口返回 `status != 1` 时会抛出包含 `info/infocode` 的错误
- 返回内容为 JSON 字符串，便于 LLM 工具链直接消费

## 8. 可扩展方向

- 增加“地址到地址”一体化导航工具（内部自动 geocode -> route）
- 增加多策略驾车对比（strategy 10/12/13 等）
- 增加路径 polyline 精简与可视化输出（GeoJSON）
- 接入高德路径规划 2.0 / 高级路径规划接口
