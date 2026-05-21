# Web前端界面

## 技术栈

- Vue 3 (Composition API, `<script setup>`)
- Vite 构建工具
- 原生实现（无 UI 组件库依赖）
- 高德地图 JSAPI v2.0 (WebGL)

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

### 3. 启动 OpenCode 服务器

```bash
opencode serve --cors http://localhost:8080
```

说明：
- `--cors` 参数允许前端页面跨域访问
- 默认端口 4096

### 4. 启动 Web 服务器

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
- 子智能体调用嵌套展示（工具/skills 状态实时更新）

## 架构概览

```
ChatPanel.vue
├── SSE /global/event → 实时流式渲染（文本/推理/工具）
│   ├── message.part.delta     → 增量文本 → 累加渲染
│   ├── message.part.updated   → 最终部件（文本/推理/工具）
│   └── session.status         → busy/idle 状态
│
├── POST /session/{id}/message → 最终对账（仅更新工具状态）
│   └── applyFinalResponse()
│       ├── text: 跳过（SSE 已处理）
│       └── tool: addToolCallMsg 去重更新
│
└── GET /command → 工具分类映射
    └── commandSourceMap[name] = "command"|"mcp"|"skill"
```

## 消息渲染模型

消息存储在扁平数组 `messages.value` 中，每条消息有 `type` 字段区分渲染方式：

| `type` | 渲染方式 | 关键字段 |
|--------|----------|---------|
| `message` (role=user) | 蓝色右对齐气泡 | `content`, `points`, `userText` |
| `message` (role=assistant) | 白色左对齐气泡 + Markdown | `content`, `typing`, `loading` |
| `reasoning` | 可折叠 `<details>` 思考块 | `content`, `expanded` |
| `tool_call` | 工具调用卡片 | `toolName`, `status`, `input`, `output`, `agent`, `_subTools` |
| `tool_chain` | 工具调用链摘要（可折叠） | `steps` |
| `system` | 居中灰色系统消息 | `content` |

## OpenCode SSE 事件流解析

前端通过原生 `EventSource` 连接 `/global/event` 端点。通信为标准 SSE 协议（`data: ...\n\n`），**不支持** `addEventListener` 命名事件——所有事件走 `onmessage`。

### 事件包裹结构

```json
{
  "payload": {
    "id": "evt_xxx",
    "type": "<event_type>",
    "properties": { ... }
  }
}
```

事件类型位于 `payload.type`，数据位于 `payload.properties`。

### 关键事件类型

| `payload.type` | 触发时机 | 关键 `properties` 字段 |
|---|---|---|
| `session.status` | 会话忙/闲切换 | `sessionID`, `status: { type: "busy"\|"idle" }` |
| `message.updated` | 消息元数据变更 | `sessionID`, `info: { id, role, agent }` |
| `message.part.updated` | 部件创建/更新 | `sessionID`, `part: Part` |
| `message.part.delta` | 流式文本增量 | `sessionID`, `messageID`, `partID`, `field: "text"`, `delta` |

### Part 类型

`message.part.updated` 的 `part.type` 决定渲染方式：

| `part.type` | 渲染组件 | 关键字段 |
|---|---|---|
| `text` | 助手文本气泡 | `part.text` |
| `reasoning` | `<details>` 可折叠思考块 | `part.text` |
| `tool` | 工具调用卡片 | `part.tool`, `part.state`, `part.sessionID` |
| `step-start/step-finish/snapshot/patch` | 跳过 | — |

## 核心渲染逻辑

### 1. 过滤用户消息回显

服务端会将用户输入作为 `message.part.updated(type=text)` 回传。通过 `messageID` 区分：

```
message.updated(role="user")  →  记录 info.id 为 currentUserMessageId
message.part.delta/updated    →  检查 part.messageID
  ├── === currentUserMessageId → 跳过（属于 user 消息）
  └── !== currentUserMessageId → 渲染（属于 assistant 消息）
```

### 2. 推理与回答分离

`message.part.delta` 不携带 part 类型（均使用 `field: "text"`），通过 `partID` 关联：

```
partTypeByID[part.id] = part.type  ← 在 message.part.updated 时记录

message.part.updated(type=reasoning, id="prt_A")
  → partTypeByID["prt_A"] = "reasoning"
  → 创建空的 reasoning 占位
message.part.delta(partID="prt_A", delta="...")
  → 查找 partTypeByID["prt_A"] → "reasoning"
  → 更新 reasoning 块 content

message.part.updated(type=text, id="prt_B")
  → partTypeByID["prt_B"] = "text"
  → 创建空的文本气泡占位
message.part.delta(partID="prt_B", delta="...")
  → 查找 partTypeByID["prt_B"] → "text"
  → 填充文本气泡，typing 闪烁
```

### 3. 工具调用渲染

工具部件通过 `addToolCallMsg` 创建/更新卡片：

```
message.part.updated(type=tool, tool="task", state={status:"pending", ...})
  → status === "pending" → 跳过

message.part.updated(type=tool, tool="task", state={status:"running", metadata:{sessionId:"ses_child"}})
  → addToolCallMsg("task", "running", ..., "ses_child", agentName)
  → 创建 tool_call 卡片，_expanded: false
  → subSessionIds.add("ses_child")
  → subAgentNames["ses_child"] = agentName
```

### 4. 子智能体工具嵌套

子会话（child session）的事件通过 `subSessionIds` 白名单放行：

```
handleGlobalEvent → 检查 props.sessionID
  ├── === currentSessionId → 放行（主会话）
  ├── in subSessionIds → 放行（子会话）
  └── 其他 → 丢弃
```

子会话的工具/文本/推理不创建独立消息，嵌套到父 `task` 卡片：

```
task 卡片 (parent.subSessionId === "ses_child")
├── _subTools[]   ← 子工具列表
│   ├── { tool: "geocode", status, input, output }
│   └── { tool: "route_planning", status, input, output }
├── _subReasoning ← 子智能体思考过程
├── _subText      ← 子智能体文本回复
├── _toolCount    ← 工具计数
├── _skillCount   ← skill 计数
└── _subStatusText ← 实时状态文本
```

header 中通过 `.sub-agent-indicator` 展示实时状态：

| 状态 | `_subStatusText` | 设置位置 |
|------|-----------------|---------|
| 卡片创建 | `等待中...` | `addToolCallMsg` |
| 子智能体思考 | `思考中...` | `handlePartUpdated` reasoning case |
| 子智能体调用工具 | `调用工具: {toolName}` | `handlePartUpdated` tool case |
| 子智能体回复 | `回复中...` | `handlePartUpdated` text case |
| 全部完成 | `已完成 ({countLabel})` | tool completion 或 POST 响应 |

### 5. 工具 vs Skill 分类

从 `GET /command` 获取命令列表，每个命令有 `source` 字段：

```json
[
  { "name": "bash", "source": "command" },
  { "name": "geocode", "source": "mcp" },
  { "name": "geodecode", "source": "mcp" }
]
```

构建 `commandSourceMap[name] → source`。工具计数时查表：

```
source === "skill" → _skillCount++
其余（"command" / "mcp" / 未找到）→ _toolCount++
```

### 6. POST 响应仅对账不覆盖

`POST /session/{id}/message` 响应达到后，`applyFinalResponse` 执行：

1. **跳过 text 部件** — SSE 已流式渲染完毕
2. **工具部件** → `addToolCallMsg` 去重更新（pending→running→completed）
3. **关闭 typing 光标**
4. **不删除、不创建 SSE 消息**

### 7. 自动滚动

发送消息后自动滚动到底部，使新消息和 AI 回复可见：

```javascript
function scrollToBottom() {
  nextTick(() => {
    requestAnimationFrame(() => {
      const el = messagesRef.value
      if (el) el.scrollTop = el.scrollHeight
    })
  })
}
```

## 数据流时序

```
用户输入
    ↓
POST /session/{id}/message   → 返回 { parts: [...] }
    │
    ├─ SSE /global/event 并行到达：
    │   message.updated(role=user)       → 记录 currentUserMessageId
    │   message.part.updated(text, echo) → 跳过（隶属 userMessageId）
    │   message.updated(role=assistant)  → 创建 assistant message
    │   message.part.updated(reasoning)  → 创建推理块占位
    │   message.part.delta               → 增量填充推理/文本
    │   message.part.updated(reasoning)  → 推理完成
    │   message.part.updated(text, "")   → 创建文本气泡占位
    │   message.part.updated(tool, task) → 创建 task 卡片 + 注册子会话
    │   [子会话事件]:
    │   message.part.updated(reasoning)  → → 追加到父卡片 _subReasoning
    │   message.part.delta               → → 累加到父卡片 _subReasoning/_subText
    │   message.part.updated(tool)       → → 追加到父卡片 _subTools[]
    │   message.part.updated(text)       → → 追加到父卡片 _subText
    │   message.part.updated(tool, completed) → 更新 _subStatusText
    │   session.status(idle)             → 会话空闲
    │
    └─ POST 返回后：
         applyFinalResponse()
         ├─ text: 跳过
         └─ tool: addToolCallMsg 去重
```

## 地图点标注功能

用户可在对话时在地图上添加点标记，这些标记会作为上下文发送给 LLM。

### 操作方式

1. 点击对话面板顶部的图钉按钮（蓝色高亮表示已开启），进入标注模式
2. 地图光标变为十字准星，点击任意位置自动生成带字母标签的蓝色圆形标记（A, B, C...）
3. 点击标记右上角的 × 可删除该标记，被删除的标签可被后续新标记复用
4. 再次点击图钉按钮可退出标注模式

### 发送至 LLM 的格式

```
[地图标注点]
A (116.397000, 39.909000)
B (116.400000, 39.910000)

[用户问题]
这两个点之间距离多远？
```

- 坐标保留 6 位小数
- 前端 UI 内以卡片形式展示标注点，用户原文单独显示

### 生命周期

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
├── index.html            # 入口页面
├── package.json          # 项目配置
├── vite.config.js        # Vite配置
└── src/
    ├── main.js           # 入口文件
    ├── App.vue           # 根组件（地图 + 对话面板 + 品牌标识）
    └── components/
        ├── ChatPanel.vue     # 对话面板（~1750行）
        └── MapContainer.vue  # 地图容器
```
