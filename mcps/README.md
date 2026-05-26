# GIS MCP Server

将 GIS 能力封装为 MCP tools，供 AI 助手调用。当前后端使用高德地图 API，后续将切换为 DBRG。

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `AMAP_API_KEY` | 地图服务 API Key（当前为高德 Key） | **必填** |
| `DATA_SERVER_URL` | 前端数据服务地址 | `http://localhost:8000` |

项目根目录 `.env` 文件自动加载。

## Tools

### `geocode(address, city?)`

地理编码——地址转坐标。结果推送到 data server `points` 通道。

### `geodecode(location)`

逆地理编码——坐标转地址。结果推送到 data server `points` 通道。

### `route_planning(origin, destination, origin_formatted_address?, destination_formatted_address?, mode?, strategy?)`

路径规划。`mode` 可选 `driving` / `walking` / `bicycling`，`strategy` 仅对驾车有效（默认 0）。
`origin_formatted_address` / `destination_formatted_address` 为起点/终点地址文本。
推送到 data server `polyline` 通道的数据包含起点/终点信息 + 路径分段坐标，返回结果中已剔除 `polyline` 字段。

### `direction_distance(loc1, loc2, origin_formatted_address?, destination_formatted_address?)`

计算两点直线距离（米）。`origin_formatted_address` / `destination_formatted_address` 为起点/终点地址文本。
结果推送到 data server `distance` 通道，包含起点/终点坐标、地址及距离。

### `set_final(isFinal)`

标记当前推送的数据是否为最终结果。

## 返回格式

各工具返回的 JSON 结构详见 [`api/README.md`](../api/README.md)。
