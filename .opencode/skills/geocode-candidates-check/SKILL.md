---
name: geocode-candidates-check
description: 当地图地理编码返回多个候选结果时，强制让用户确认选择正确的地址
compatibility: opencode
metadata:
  audience: users
  workflow: gis
---

## What I do当地图地理编码接口返回 `candidates` 参数大于 1 时，必须询问用户确认具体要选择哪个区域或地址。

## When to use me

- 调用 `amap_gis_geocode` 后
- 检查返回结果中的 `candidates` 参数值
- 如果 `candidates > 1`，立即询问用户：需要哪个具体区域？然后根据用户的回答重新调用接口并限定 city 参数
- 如果 `candidates = 1`，直接返回唯一结果

## 执行流程

1. 调用 `amap_gis_geocode` 获取地址经纬度
2. 检查返回的 `candidates` 值
3. **如果 candidates > 1**：
   - 询问用户："返回了 N 个候选结果，您想选择哪个？"
   - 等待用户回复具体区域后，使用 `city` 参数重新查询
4. **如果 candidates = 1**：返回该结果

## 重要规则

- **严禁**在 candidates > 1 时直接返回第一个结果
- **必须**让用户明确选择
- 询问示例："返回了 2 个候选结果，请问您想选择北京市还是天津市？"