# GIS Data Server

## 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/data` | 获取当前数据（返回 `{}` 或 `{ type, data, isFinal }`） |
| `POST` | `/api/set` | 设置数据 |
| `PATCH` | `/api/final` | 标记是否最终数据 |
| `WS` | `/ws/data` | WebSocket 实时推送数据变更 |

WebSocket 客户端连接后立即收到当前数据，后续每次数据更新自动推送。

---

## 数据格式详情

以下根据 `mcps/server.py` 中各工具调用 `_set(typ, data)` 的实际情况，列出所有可能的 `type` 及对应的 `data` 结构。

### 1. `type = "points"` — 坐标点

**来源**: `geocode` / `geodecode` 工具

#### geocode（地理编码 — 地址转坐标）

```json
{
  "type": "points",
  "isFinal": false,
  "data": [
    {
      "formatted_address": "北京市朝阳区阜通东大街6号",
      "location": {"lng": 116.482086, "lat": 39.990496}
    }
  ]
}
```

#### geodecode（逆地理编码 — 坐标转地址）

```json
{
  "type": "points",
  "isFinal": false,
  "data": [
    {
      "location": {"lng": 116.482145, "lat": 39.990039},
      "address": "河北省廊坊市永清县韩村镇506乡道"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `formatted_address` / `address` | `string` | 地址描述 |
| `location` | `object` | `{ lng: number, lat: number }` 经纬度 |

---

### 2. `type = "polyline"` — 路径折线

**来源**: `route_planning` 工具

`data[0]` 为起点/终点元信息，后续元素为路径分段。

```json
{
  "type": "polyline",
  "isFinal": false,
  "data": [
    {
      "origin": {"lng": 116.434327, "lat": 39.909045, "address": "北京市东城区建国门"},
      "destination": {"lng": 116.434818, "lat": 39.908655, "address": "北京市东城区朝阳门"}
    },
    {
      "instruction": ["向东骑行54米右转", "沿建国门北大街向南骑行112米右转"],
      "polyline": [
        {"lng": 116.434327, "lat": 39.909045},
        {"lng": 116.434965, "lat": 39.909045},
        {"lng": 116.434931, "lat": 39.908932}
      ]
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `origin` | `object` | `{ lng, lat, address }` 起点坐标及地址 |
| `destination` | `object` | `{ lng, lat, address }` 终点坐标及地址 |
| `instruction` | `string[]` | 每段路线的文字指引 |
| `polyline` | `object[]` | 路径坐标点数组，每项为 `{ lng: number, lat: number }` |

> 注意：`route_planning` 工具返回给调用者的结果中会剔除 `polyline` 字段，仅推送至 data server。

---

### 3. `type = "distance"` — 直线距离

**来源**: `direction_distance` 工具

```json
{
  "type": "distance",
  "isFinal": false,
  "data": [
    {
      "origin": {"lng": 116.397428, "lat": 39.90923, "address": "北京市东城区东直门"},
      "destination": {"lng": 116.417428, "lat": 39.92923, "address": "北京市东城区雍和宫"},
      "distance": 2500.0
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `origin` | `object` | `{ lng: number, lat: number, address: string }` 起点坐标及地址 |
| `destination` | `object` | `{ lng: number, lat: number, address: string }` 终点坐标及地址 |
| `distance` | `number` | 两点直线距离（单位：米） |
