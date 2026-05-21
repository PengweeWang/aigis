# Web前端界面

## 技术栈

- Vue 3
- Vite 构建工具
- 原生实现（无 UI 组件库依赖）

## 启动步骤

### 1. 配置地图密钥

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入高德地图 Web API 的 Key 和 Security Code：

```
VITE_AMAP_KEY=your_amap_web_api_key_here
VITE_AMAP_SECURITY_CODE=your_amap_security_code_here
```

### 2. 安装依赖

```bash
cd web
npm install
```

### 3. 启动OpenCode服务器

在项目根目录运行：

```bash
opencode serve --cors http://localhost:8080
```

说明：
- `--cors` 参数允许前端页面跨域访问
- 默认端口 4096

### 4. 启动Web服务器

```bash
npm run dev
```

### 5. 访问界面

打开浏览器访问：`http://localhost:8080`

## 功能说明

- 左侧悬浮面板：与 gis-orchestrator 智能体对话
- 底层：高德地图界面
- 支持新建会话、发送消息
- 流式输出：通过 SSE 实时展示文本、思考过程和工具调用

## OpenCode SSE 事件流解析

前端通过原生 `EventSource` 连接 OpenCode 服务端的 `/global/event` 端点获取实时事件。通信为标准 SSE 协议（`data: ...\n\n`），**不支持** `EventSource` 的 `addEventListener` 命名事件——所有事件走 `onmessage`。

### 事件包裹结构

所有事件 JSON 遵循统一包裹结构：

```json
{
  "payload": {
    "id": "evt_xxx",
    "type": "<event_type>",
    "properties": { ... }
  }
}
```

注意：事件类型位于 `payload.type`，数据位于 `payload.properties`，而非顶层。

### 关键事件类型

| `payload.type` | 触发时机 | 关键 `properties` 字段 |
|---|---|---|
| `session.status` | 会话忙/闲状态切换 | `sessionID`, `status: { type: "busy"\|"idle" }` |
| `message.updated` | 消息元数据变更 | `sessionID`, `info: { id, role, agent }` |
| `message.part.updated` | 部件创建/更新 | `sessionID`, `part: Part` |
| `message.part.delta` | 流式文本增量推送 | `sessionID`, `messageID`, `partID`, `field: "text"`, `delta: string` |

### Part 类型

`message.part.updated` 的 `part.type` 决定如何处理：

| `part.type` | 渲染方式 | 关键字段 |
|---|---|---|
| `text` | 助手文本气泡 | `part.text` |
| `reasoning` | 可折叠思考块（`<details>`） | `part.text` |
| `tool` | 工具调用卡片 | `part.tool`, `part.state.status`, `part.state.input`, `part.state.output`, `part.state.metadata` |
| `step-start` / `step-finish` / `snapshot` / `patch` | 跳过，内部部件 | — |

### 渲染规则

**1. 过滤用户消息回显**

服务端通过 `message.updated`、`message.part.updated` 将用户消息原样回传。按 `messageID` 过滤：

```
message.updated(role="user")  →  记录 info.id 为 currentUserMessageId
message.part.delta/updated    →  检查 part.messageID
  ├── === currentUserMessageId → 跳过（用户消息部件）
  └── !== currentUserMessageId → 正常渲染（助手部件）
```

**2. 推理文本与回答文本分离**

`message.part.delta` 事件不携带 part 类型，推理过程和最终回答都使用 `field: "text"`。通过部件的 `partID` 关联：

```
message.part.updated(type=reasoning, id="prt_A")
  → 创建空的 <details class="thinking-block"> 占位
message.part.delta(partID="prt_A", delta="...")
  → 查找 _partId="prt_A" 的 reasoning 块，更新 content
message.part.updated(type=reasoning, id="prt_A", text="完整推理")
  → 最终内容写入 reasoning 块

message.part.updated(type=text, id="prt_B", text="")
  → 创建空的文本气泡占位（loading 动画）
message.part.delta(partID="prt_B", delta="...")
  → 查找 _partId="prt_B" 的文本气泡，填充 content，切换 typing 光标
message.part.updated(type=text, id="prt_B", text="完整回答")
  → 最终文本写入气泡，关闭 typing 光标
```

**3. POST 响应仅用于最终文本对账**

```
POST /session/{id}/message 返回 { parts: [...] }
  → 不删除 SSE 已渲染的消息
  → 从 parts 中提取最终文本（跳过匹配用户输入的部分）
  → 查找已有的 SSE 文本气泡（m._sse && type=message）→ 直接更新 content
  → 若不存在 SSE 气泡 → addMessage 创建新消息
  → 工具部件 → addToolCallMsg 去重更新
```

**4. 工具调用去重**

同一工具可能收到多次 `message.part.updated`（状态从 pending→running→completed）。按 `toolName + status=running` 查找已有卡片：

- 找到 → 更新 `status`、`input`、`output`
- 未找到 → 创建新卡片

### 数据流时序

```
用户输入 → POST /session/{id}/message
             │
             ├─ SSE /global/event 并行到达：
             │   message.updated(role=user)       → 记录 userMessageId
             │   message.part.updated(text,echo)   → 跳过（隶属 userMessageId）
             │   message.updated(role=assistant)   → 记录 assistantMessageId
             │   message.part.updated(reasoning)   → 创建推理块占位
             │   message.part.delta(reasoning)     → 填充推理内容
             │   message.part.updated(reasoning)   → 推理完成
             │   message.part.updated(text,"")     → 创建文本气泡占位
             │   message.part.delta(text)          → 流式填充文本
             │   message.part.updated(tool)        → 创建/更新工具卡片
             │   message.part.updated(text,final)  → 文本最终态
             │   session.status(idle)              → 会话空闲
             │
             └─ POST 返回 { parts: [...] }
                  applyFinalResponse()
                  ├─ 提取最终文本 → 更新 SSE 文本气泡 content
                  └─ 工具部件 → addToolCallMsg 去重更新
```

### 地图点标注功能

用户可在对话时在地图上添加点标记，这些标记会作为上下文发送给 LLM。

#### 操作方式

1. 点击对话面板顶部的图钉按钮（蓝色高亮表示已开启），进入标注模式
2. 地图光标变为十字准星，点击任意位置自动生成带字母标签的蓝色圆形标记（A, B, C...）
3. 点击标记右上角的 × 可删除该标记，被删除的标签可被后续新标记复用
4. 再次点击图钉按钮可退出标注模式

#### 发送至 LLM 的格式

发送消息时，当前所有地图标注点会被自动拼接到用户消息最前面，格式如下：

```
[地图标注点]
A (116.397000, 39.909000)
B (116.400000, 39.910000)

[用户问题]
这两个点之间距离多远？
```

- 坐标保留 6 位小数
- 此格式仅用于发送给 LLM 的消息体；前端 UI 内以卡片形式友好展示标注点，用户原文单独显示

#### 生命周期

| 操作 | 系统标记（LLM查询结果） | 用户标注点 |
|------|------------------------|-----------|
| 发送新消息 | 清除 | 保留 |
| 新建会话 | 清除 | 清除 |
| 手动点击 × | — | 清除该点 |

- **系统标记**：由 LLM 通过 WebSocket 推送的地理编码/路径规划结果渲染，每次新查询开始时清除
- **用户标注点**：通过标注模式手动添加，跨对话轮次持久保留，仅新建会话或手动删除时清除

## 目录结构

```
web/
├── index.html        # 入口页面
├── package.json     # 项目配置
├── vite.config.js   # Vite配置
└── src/
    ├── main.js      # 入口文件
    ├── App.vue      # 根组件
    └── components/
        ├── ChatPanel.vue   # 对话面板
        └── MapContainer.vue # 地图容器
```