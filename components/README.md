# OpenCodeChatPanel

一个可插拔的 Vue 3 聊天面板组件，专为 [OpenCode](https://opencode.ai) 设计，支持智能体切换、流式输出、工具调用展示、Markdown 渲染等功能。

## 安装

```bash
cp OpenCodeChatPanel.vue 你的项目/components/
```

依赖：Vue 3（无其他第三方依赖）。

## 快速开始

```vue
<template>
  <OpenCodeChatPanel
    v-model:messages="messages"
    :agents="agents"
    v-model:selectedAgent="selectedAgent"
    :sessionBusy="sessionBusy"
    :modelOptions="modelOptions"
    v-model:selectedModel="selectedModel"
    @send="handleSend"
    @abort="handleAbort"
    @new-session="handleNewSession"
  />
</template>

<script setup>
import { ref } from 'vue'
import OpenCodeChatPanel from './OpenCodeChatPanel.vue'

const messages = ref([])
const sessionBusy = ref(false)
const selectedAgent = ref('assistant')
const selectedModel = ref('')
const modelOptions = ref([])

const agents = ref([])

const AGENT_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f97316', '#ef4444']

async function fetchAgents() {
  const r = await fetch('/api/agent')  // 或 http://127.0.0.1:4096/agent
  const list = await r.json()
  agents.value = list
    .filter(a => !a.hidden && a.mode === 'primary')
    .map((a, i) => ({
      value: a.name,
      label: a.name,
      color: a.color || AGENT_COLORS[i % AGENT_COLORS.length],
    }))
}

function handleSend({ text, agent, model }) {
  // 发送消息到你的后端 API
}

function handleAbort() {
  // 中止当前请求
}

function handleNewSession() {
  // 创建新会话
}
</script>
```

## Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `title` | `string` | `'AI Chat'` | 面板标题 |
| `messages` | `array` | `[]` | 消息列表（支持 `v-model`） |
| `sessionBusy` | `boolean` | `false` | 会话是否繁忙 |
| `agents` | `array` | `[]` | 智能体列表 `[{value, label, color}]` |
| `selectedAgent` | `string` | `''` | 当前选中的智能体（支持 `v-model`） |
| `modelOptions` | `array` | `[]` | 模型选项 `[{value, label}]` |
| `selectedModel` | `string` | `''` | 当前选中的模型（支持 `v-model`） |
| `panelWidth` | `number` | `450` | 面板宽度（支持 `v-model`） |
| `placeholder` | `string` | `'请输入您的问题...'` | 输入框占位文字 |
| `showModelSelect` | `boolean` | `true` | 是否显示模型选择器 |
| `showNewSession` | `boolean` | `true` | 是否显示新建会话按钮 |
| `showPointAdd` | `boolean` | `false` | 是否显示标注模式按钮 |
| `pointAddMode` | `boolean` | `false` | 标注模式状态（配合地图使用） |
| `userPointsCount` | `number` | `0` | 用户标注点数量 |

## Events

| 事件 | 载荷 | 说明 |
|------|------|------|
| `send` | `{ text, agent, model }` | 用户发送消息 |
| `abort` | — | 用户点击停止 |
| `new-session` | — | 用户点击新建会话 |
| `toggle-point-add` | — | 用户切换标注模式 |
| `update:selectedAgent` | `value` | 智能体切换 |
| `update:selectedModel` | `value` | 模型切换 |
| `update:panelWidth` | `value` | 面板宽度变化 |
| `update:pointAddMode` | `value` | 标注模式变化 |

## Slots

| 插槽 | 说明 |
|------|------|
| `header-title` | 自定义标题区域 |
| `header-actions` | 自定义头部操作按钮 |

## 消息格式

消息对象结构：

```typescript
interface Message {
  id: string
  type: 'system' | 'message' | 'reasoning' | 'tool_call' | 'tool_chain'
  content?: string
  role?: 'user' | 'assistant'
  loading?: boolean
  typing?: boolean
  expanded?: boolean
  // tool_call 专用
  toolName?: string
  status?: 'running' | 'completed' | 'failed' | 'cancelled'
  input?: any
  output?: any
  agent?: string
  subSessionId?: string
  subStatus?: string
  _expanded?: boolean
  _subTools?: any[]
  _subReasoning?: string
  _subText?: string
  // tool_chain 专用
  steps?: Array<{ title: string, content?: string, status: string }>
  // user 消息专用
  points?: Array<{ label: string, lng: number, lat: number }>
  userText?: string
}
```

## 示例

参考 `ExampleChat.vue` 查看完整集成示例，包括 SSE 流式通信、会话管理、工具调用处理等。
