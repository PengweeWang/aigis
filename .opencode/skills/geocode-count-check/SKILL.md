---
name: geocode-count-check
description: 当地图地理编码返回多个候选结果时，强制让用户确认选择正确的地址
compatibility: opencode
metadata:
  audience: users
  workflow: gis
---

## What I do

当地图地理编码接口返回 `count`（字符串类型）大于 1 时，必须询问用户确认具体要选择哪个地址。

## When to use me

- 调用 `amap_gis_geocode` 后
- 检查返回结果中的 `count` 和 `status` 字段
- 如果 `count > 1`，立即展示所有候选 `formatted_address` 让用户选择，并从已返回的结果中提取对应坐标
- 如果 `count = 1`，直接返回唯一结果

## 执行流程

1. 调用 `amap_gis_geocode` 获取地址经纬度
2. 检查返回结果：
   - 若 `status ≠ "1"`，报错并终止
   - 若 `count = "0"`，报错"未找到匹配地址"并终止
3. 读取 `count` 并转为数字：`parseInt(count)`
4. **如果 count > 1**：
   - 遍历 `geocodes` 数组，提取每条记录的 `formatted_address` 和 `district`
   - 以编号列表形式展示给用户，例如：
     ```
     找到 3 个候选地址，请选择：
     1. xxx (xx区)
     2. yyy (xx区)
     3. zzz (xx区)
     ```
   - 等待用户输入编号
   - 根据用户选择的编号，从 `geocodes[索引].location` 中提取坐标
   - **禁止重新调用接口**（结果已存在，直接使用）
5. **如果 count = 1**：直接返回 `geocodes[0].location`

## 重要规则

- **严禁**在 count > 1 时直接返回第一个结果或自动猜测
- **严禁**在用户确认后重新调用接口（候选项已包含所有结果）
- **必须**先检查 `status` 是否为 `"1"`，再处理数据
