<template>
  <div class="chat-panel" :style="{ width: panelWidth + 'px' }">
    <div class="resize-handle" @mousedown="startResize"></div>
    <div class="chat-header">
      <h3>GIS Chat</h3>
      <div class="header-actions">
        <div class="add-point-wrapper">
          <button class="icon-btn" :class="{ active: pointAddMode }" @click="togglePointAddMode" :title="pointAddMode ? '关闭标注模式' : '开启标注模式'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" :stroke="pointAddMode ? '#fff' : 'currentColor'" stroke-width="2">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
              <circle cx="12" cy="9" r="2.5"/>
            </svg>
          </button>
          <span v-if="userPointsCount > 0" class="point-badge">{{ userPointsCount }}</span>
        </div>
        <button class="icon-btn new-session-btn" @click="createNewSession" title="新建会话">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </div>

    <div class="chat-messages" ref="messagesRef">
      <template v-for="msg in messages" :key="msg.id">
        <div v-if="msg.type === 'system'" class="msg-row system">
          <div class="system-msg">{{ msg.content }}</div>
        </div>

        <div v-else-if="msg.type === 'message'" class="msg-row" :class="msg.role">
          <div class="bubble" :class="msg.role" :data-loading="msg.loading || undefined">
            <template v-if="msg.role === 'user' && msg.points">
              <div class="points-card">
                <div class="points-card-header">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#1890ff" stroke-width="2">
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                    <circle cx="12" cy="9" r="2.5"/>
                  </svg>
                  <span>地图标注点</span>
                  <span class="points-count">{{ msg.points.length }}</span>
                </div>
                <div class="points-card-body">
                  <div class="point-item" v-for="p in msg.points" :key="p.label">
                    <span class="point-label">{{ p.label }}</span>
                    <span class="point-coords">{{ p.lng.toFixed(6) }}, {{ p.lat.toFixed(6) }}</span>
                  </div>
                </div>
              </div>
              <div class="user-text">{{ msg.userText }}</div>
            </template>
            <template v-else-if="msg.role === 'assistant'">
              <div v-if="msg.loading" class="loading-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
              <div v-else class="md-content" v-html="renderMarkdown(msg.content)" :data-typing="msg.typing || undefined"></div>
            </template>
            <template v-else>
              <div class="md-content" v-html="renderMarkdown(msg.content)"></div>
            </template>
          </div>
        </div>

        <details v-else-if="msg.type === 'reasoning'" class="thinking-block" :open="msg.expanded" @toggle="msg.expanded = $event.target.open">
          <summary>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
            <span>思考过程</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 9l6 6 6-6"/>
            </svg>
          </summary>
          <div class="thinking-content md-content" v-html="renderMarkdown(msg.content)"></div>
        </details>

        <div v-else-if="msg.type === 'tool_call'" class="tool-call-card" :class="msg.status">
          <div class="tool-call-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
            <span v-if="msg.agent" class="tool-agent-badge" :style="{ '--color': agentColor(msg.agent) }">{{ msg.agent }}</span>
            <span class="tool-call-name">{{ msg.toolName }}</span>
            <template v-if="!msg.subSessionId">
              <span class="tool-call-status" :class="msg.status">
                <span class="status-dot" :class="msg.status"></span>
                {{ statusLabel(msg.status) }}
              </span>
            </template>
            <span v-if="msg.subSessionId" class="sub-agent-indicator" :class="{ running: msg.subStatus === 'running' }">
              <span v-if="msg.subStatus === 'running'" class="sub-agent-spinner"></span>
              <span class="sub-agent-text">{{ msg._subStatusText || '等待中...' }}</span>
            </span>
            <button v-if="msg.input !== undefined || msg._subTools?.length || msg._subReasoning || msg._subText" class="tool-toggle" @click="msg._expanded = !msg._expanded">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                :style="{ transform: msg._expanded ? 'rotate(180deg)' : '' }">
                <path d="M6 9l6 6 6-6"/>
              </svg>
              {{ msg._expanded ? '收起' : '详情' }}
            </button>
          </div>
          <div v-if="msg._expanded" class="tool-call-body">
            <div v-if="msg.input !== undefined" class="tool-section">
              <div class="tool-section-label">输入</div>
              <pre class="tool-code">{{ formatToolInput(msg.input) }}</pre>
            </div>
            <div v-if="msg.output !== undefined && !msg._subTools?.length" class="tool-section">
              <div class="tool-section-label">输出</div>
              <pre class="tool-code">{{ truncateOutput(msg.output) }}</pre>
            </div>
            <!-- Sub-agent tools nested inside parent card -->
            <div v-if="msg._subTools?.length" class="sub-tools">
              <div class="tool-section-label">子智能体调用</div>
              <div v-for="st in msg._subTools" :key="st.id" class="sub-tool-item" :class="st.status">
                <div class="sub-tool-header">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
                  </svg>
                  <span class="sub-tool-name">{{ st.tool }}</span>
                  <span class="tool-call-status" :class="st.status">
                    <span class="status-dot" :class="st.status"></span>
                    {{ statusLabel(st.status) }}
                  </span>
                  <button v-if="st.input !== undefined" class="tool-toggle" @click="st._expanded = !st._expanded">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                      :style="{ transform: st._expanded ? 'rotate(180deg)' : '' }">
                      <path d="M6 9l6 6 6-6"/>
                    </svg>
                    {{ st._expanded ? '收起' : '详情' }}
                  </button>
                </div>
                <div v-if="st._expanded" class="sub-tool-body">
                  <div v-if="st.input !== undefined" class="tool-section">
                    <div class="tool-section-label">输入</div>
                    <pre class="tool-code">{{ formatToolInput(st.input) }}</pre>
                  </div>
                </div>
              </div>
            </div>
            <!-- Sub-agent reasoning & response -->
            <div v-if="msg._subReasoning" class="sub-agent-response">
              <div class="tool-section-label">智能体思考</div>
              <div class="sub-reasoning">{{ msg._subReasoning }}</div>
            </div>
            <div v-if="msg._subText" class="sub-agent-response">
              <div class="tool-section-label">智能体回复</div>
              <div class="sub-text md-content" v-html="renderMarkdown(msg._subText)"></div>
            </div>
          </div>
          <div v-if="msg.subSessionId" class="sub-agent-bar">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
            </svg>
            <span>子智能体</span>
            <span class="sub-agent-status" :class="{ active: msg.subStatus === 'running' }">
              {{ msg.subStatus === 'running' ? '运行中...' : msg.subStatus === 'completed' ? '已完成' : msg.subStatus === 'cancelled' ? '已取消' : '已结束' }}
            </span>
          </div>
        </div>

        <details v-else-if="msg.type === 'tool_chain'" class="thinking-block" :open="msg.expanded" @toggle="msg.expanded = $event.target.open">
          <summary>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            <span>工具调用链</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 9l6 6 6-6"/>
            </svg>
          </summary>
          <div class="thought-chain">
            <div v-for="(step, i) in msg.steps" :key="i" class="chain-step" :class="step.status">
              <div class="chain-step-indicator">
                <span v-if="step.status === 'completed'" class="step-icon completed">✓</span>
                <span v-else-if="step.status === 'error'" class="step-icon error">✗</span>
                <span v-else-if="step.status === 'active'" class="step-icon active"></span>
                <span v-else class="step-icon pending"></span>
              </div>
              <div class="chain-step-body">
                <div class="chain-step-title">{{ step.title }}</div>
                <div v-if="step.content" class="chain-step-content">{{ step.content }}</div>
              </div>
            </div>
          </div>
        </details>
      </template>
    </div>

    <div class="chat-input-area">
      <div class="input-toolbar">
        <div class="model-select-wrapper">
          <svg class="model-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
          </svg>
          <select v-model="selectedModel" class="model-select" @change="handleModelChange">
            <option v-for="m in modelOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>
      </div>
      <div class="input-row">
        <textarea
          v-model="inputText"
          class="chat-textarea"
          :disabled="sessionBusy"
          placeholder="请输入您的问题..."
          rows="1"
          @keydown.enter.exact.prevent="handleSend"
          @input="autoResize"
          ref="textareaRef"
        ></textarea>
        <button v-if="!sessionBusy" class="send-btn" @click="handleSend" :disabled="!inputText.trim()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
          </svg>
        </button>
        <button v-else class="stop-btn" @click="abortSession" title="停止回答">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- scroll anchor -->
    <div ref="bottomAnchorRef" class="scroll-anchor"></div>
  </div>
</template>

<script setup>
import { ref, nextTick, inject, onUnmounted } from 'vue'

const SERVER_URL = 'http://127.0.0.1:4096'
const mapContainer = inject('mapContainer')

const messagesRef = ref(null)
const textareaRef = ref(null)

const panelWidth = ref(450)
const resizing = ref(false)

const messages = ref([])
const inputText = ref('')
const currentSessionId = ref(null)
const subSessionIds = new Set()
const subAgentNames = {}  // sessionId -> agent name
const modelOptions = ref([])
const selectedModel = ref('')
const pointAddMode = ref(false)
const userPointsCount = ref(0)
const sessionBusy = ref(false)
const streamingPartId = ref(null)

const AGENT_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f97316', '#ef4444']
const agentColorMap = {}
function agentColor(name) {
  if (!name) return '#6366f1'
  if (!agentColorMap[name]) agentColorMap[name] = AGENT_COLORS[Object.keys(agentColorMap).length % AGENT_COLORS.length]
  return agentColorMap[name]
}

const TOOL_STATUS_LABELS = {
  running: '运行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

// Track tool source from /command endpoint
const commandSourceMap = {}  // toolName -> 'command' | 'mcp' | 'skill'

function statusLabel(s) {
  return TOOL_STATUS_LABELS[s] || s || '等待中'
}

function countLabel(toolCount, skillCount) {
  const parts = []
  if (toolCount) parts.push(`${toolCount} tool${toolCount > 1 ? 's' : ''}`)
  if (skillCount) parts.push(`${skillCount} skill${skillCount > 1 ? 's' : ''}`)
  return parts.join(' + ') || '0 tools'
}

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

// --- Markdown renderer ---

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function renderMarkdown(text) {
  if (!text) return ''
  let html = escapeHtml(text)

  // Code blocks (fenced) - must be before other block handling
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const langClass = lang ? ` class="lang-${escapeHtml(lang)}"` : ''
    return `<pre${langClass}><code>${code}</code></pre>`
  })

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  // Headers
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  // Bold, italic, strikethrough
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/~~(.+?)~~/g, '<del>$1</del>')

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')

  // Unordered lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')

  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')

  // Horizontal rules (must be before headers since --- also matches h2)
  html = html.replace(/^---+\s*$/gm, '<hr>')

  // Blockquotes
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote><p>$1</p></blockquote>')
  // Collapse adjacent blockquotes into one
  html = html.replace(/<\/blockquote>\n<blockquote>/g, '\n')

  // Tables
  html = html.replace(/^\|(.+)\|\n\|[-| :]+\|\n(\|.+\|\n?)+/gm, (match) => {
    const rows = match.trim().split('\n')
    const headerCells = rows[0].slice(1, -1).split('|').map(c => c.trim())
    // Skip separator row (rows[1])
    const bodyRows = rows.slice(2)
    let table = '<table>'
    table += '<thead><tr>' + headerCells.map(c => `<th>${c}</th>`).join('') + '</tr></thead>'
    if (bodyRows.length) {
      table += '<tbody>'
      for (const row of bodyRows) {
        const cells = row.slice(1, -1).split('|').map(c => c.trim())
        table += '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>'
      }
      table += '</tbody>'
    }
    table += '</table>'
    return table
  })

  // Paragraphs (double newlines)
  const parts = html.split(/\n\n+/)
  html = parts.map(p => {
    p = p.trim()
    if (!p) return ''
    if (p.startsWith('<h') || p.startsWith('<pre') || p.startsWith('<ul') || p.startsWith('<ol') || p.startsWith('<table') || p.startsWith('<hr') || p.startsWith('<blockquote')) return p
    // Single line breaks within a paragraph become <br>
    p = p.replace(/\n/g, '<br>')
    return `<p>${p}</p>`
  }).join('')

  return html
}

// --- UI ---

function autoResize() {
  const el = textareaRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }
}

function startResize(e) {
  resizing.value = true
  const startX = e.clientX
  const startW = panelWidth.value
  function onMove(ev) {
    panelWidth.value = Math.max(280, Math.min(800, startW + ev.clientX - startX))
  }
  function onUp() {
    resizing.value = false
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
  e.preventDefault()
}

function scrollToBottom() {
  nextTick(() => {
    const el = messagesRef.value
    if (!el) return
    requestAnimationFrame(() => {
      el.scrollTop = el.scrollHeight
    })
  })
}

function scrollToTop() {
  nextTick(() => {
    const el = messagesRef.value
    if (el) el.scrollTop = 0
  })
}

// --- Session management ---

async function checkServerHealth() {
  try {
    const r = await fetch(`${SERVER_URL}/global/health`)
    if (r.ok) {
      const d = await r.json()
      addSystemMessage(`已连接至GIS智能体，版本: ${d.version}`)
      return true
    }
  } catch {
    addSystemMessage('无法连接到OpenCode服务器，请确保已运行 opencode serve')
  }
  return false
}

async function createSession() {
  try {
    const r = await fetch(`${SERVER_URL}/session`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
    if (r.ok) {
      const s = await r.json()
      currentSessionId.value = s.id
      return true
    }
  } catch {
    addSystemMessage('创建会话失败')
  }
  return false
}

async function createNewSession() {
  messages.value = []
  mapContainer?.clearMarkers?.()
  mapContainer?.clearPolylines?.()
  mapContainer?.clearUserPoints?.()
  userPointsCount.value = 0
  sessionBusy.value = false
  streamingPartId.value = null
  subSessionIds.clear()
  await createSession()
  addSystemMessage('已创建新会话')
}

function addSystemMessage(text) {
  messages.value.push({ id: uid(), type: 'system', content: text })
  scrollToBottom()
}

function addMessage(role, content, extra = {}) {
  messages.value.push({ id: uid(), type: 'message', role, content, ...extra })
  scrollToBottom()
}

function addReasoningMessage(text) {
  messages.value.push({ id: uid(), type: 'reasoning', content: text, expanded: false })
  scrollToBottom()
}

function addToolCallMsg(toolName, status, input, output, subSessionId, agentName) {
  // Don't render pending state — wait for running/completed with actual data
  if (status === 'pending') return null

  const existing = messages.value.find(m =>
    m.type === 'tool_call' && m.toolName === toolName && (m.status === 'running' || m.status === 'pending')
  )
  if (existing) {
    existing.status = status
    if (output !== undefined) existing.output = output
    if (subSessionId && !existing.subSessionId) existing.subSessionId = subSessionId
      if (status === 'completed' && existing.subSessionId) {
        const tc = existing._toolCount || 0
        const sc = existing._skillCount || 0
        if (existing._subText) {
          existing._subStatusText = `已完成 (${countLabel(tc, sc)})`
        } else {
          existing._subStatusText = `等待回复... (${countLabel(tc, sc)})`
        }
      }
      return existing
  }
  const msg = {
    id: uid(),
    type: 'tool_call',
    toolName,
    status,
    input,
    output,
    subSessionId,
    subStatus: subSessionId ? 'running' : undefined,
    agent: agentName,
    _expanded: false,
  }
  messages.value.push(msg)
  scrollToBottom()
  return msg
}

function addToolChainMsg(steps) {
  messages.value.push({
    id: uid(),
    type: 'tool_chain',
    steps: steps.map(s => ({ title: s.title, content: s.content, status: s.status || 'pending' })),
    expanded: true,
  })
  scrollToBottom()
}

async function fetchModels() {
  try {
    const r = await fetch(`${SERVER_URL}/config/providers`)
    if (!r.ok) return
    const data = await r.json()
    const options = []
    for (const provider of data.providers || []) {
      for (const model of Object.values(provider.models || {})) {
        options.push({ value: model.id, providerID: model.providerID, label: `${provider.name} - ${model.name || model.id}` })
      }
    }
    if (options.length === 0) return
    modelOptions.value = options
    selectedModel.value = options.find(o => o.value === 'minimax-m2.5-free')?.value || options[0].value
  } catch { /* ignore */ }
}

async function fetchCommands() {
  try {
    const r = await fetch(`${SERVER_URL}/command`)
    if (!r.ok) return
    const list = await r.json()
    for (const cmd of list) {
      if (cmd.source) commandSourceMap[cmd.name.toLowerCase()] = cmd.source
    }
  } catch { /* ignore */ }
}

function handleModelChange() {}

function togglePointAddMode() {
  pointAddMode.value = !pointAddMode.value
  if (pointAddMode.value) mapContainer?.enableAddMode?.()
  else mapContainer?.disableAddMode?.()
}

function updateUserPointsCount() {
  userPointsCount.value = mapContainer?.getUserPoints?.()?.length || 0
}

function formatToolInput(input) {
  if (typeof input === 'string') return input
  try { return JSON.stringify(input, null, 2) } catch { return String(input) }
}

function truncateOutput(out) {
  if (!out) return ''
  const s = typeof out === 'string' ? out : JSON.stringify(out, null, 2)
  return s.length > 2000 ? s.slice(0, 2000) + '\n... (已截断)' : s
}

// --- SSE streaming (official opencode event format) ---
// Server sends: { payload: { type: "session.status"|"message.part.delta"|"message.part.updated", properties: { ... } } }

let eventSource = null
let eventReconnectTimer = null

// Accumulate streaming text deltas by partID
const deltaAccum = {}
const partTypeByID = {}
// Track current user message ID to filter out echoed user-message parts from SSE
let currentUserMessageId = null

function connectEventSource() {
  if (eventSource) return
  eventSource = new EventSource(`${SERVER_URL}/global/event`)
  eventSource.onmessage = (e) => {
    try {
      const event = JSON.parse(e.data)
      handleGlobalEvent(event)
    } catch {}
  }
  eventSource.onerror = () => {
    disconnectEventSource()
    eventReconnectTimer = setTimeout(connectEventSource, 3000)
  }
}

function disconnectEventSource() {
  clearTimeout(eventReconnectTimer)
  if (eventSource) {
    eventSource.onmessage = null
    eventSource.onerror = null
    eventSource.close()
    eventSource = null
  }
}

function handleGlobalEvent(event) {
  const payload = event?.payload
  if (!payload) return

  const props = payload.properties || {}
  if (!currentSessionId.value) return
  // Accept events from main session or tracked sub-sessions
  if (props.sessionID !== currentSessionId.value && !subSessionIds.has(props.sessionID)) return

  switch (payload.type) {
    case 'session.status': {
      const s = props.status?.type
      if (s === 'busy') sessionBusy.value = true
      else if (s === 'idle') {
        sessionBusy.value = false
        streamingPartId.value = null
        // Remove loading message if SSE never started
        const loading = messages.value.find(m => m.loading && m.role === 'assistant')
        if (loading) messages.value = messages.value.filter(m => m.id !== loading.id)
      }
      break
    }
    case 'message.updated': {
      if (props.info?.role === 'user') {
        currentUserMessageId = props.info.id
      }
      break
    }
    case 'message.part.delta': {
      if (props.field === 'text' && props.delta) {
        handleStreamDelta(props)
      }
      break
    }
    case 'message.part.updated': {
      if (props.part) handlePartUpdated(props.part)
      break
    }
  }
}

function handleStreamDelta(props) {
  const { partID, delta, messageID, sessionID } = props
  // Skip deltas belonging to user messages (echoed input)
  if (messageID && currentUserMessageId && messageID === currentUserMessageId) return
  // Skip if already finalized by POST response
  if (messages.value.find(m => m._finalized && m.type === 'message' && m.role === 'assistant')) return

  // Redirect sub-session deltas to parent task card
  if (sessionID && subSessionIds.has(sessionID)) {
    const parent = messages.value.find(m => m.type === 'tool_call' && m.subSessionId === sessionID)
    if (!parent) return
    deltaAccum[partID] = (deltaAccum[partID] || '') + delta
    const fullText = deltaAccum[partID]
    const ptype = partTypeByID[partID]
    if (ptype === 'reasoning') {
      parent._subReasoning = fullText
      if (parent.subStatus !== 'completed') parent._subStatusText = '思考中...'
    } else {
      parent._subText = fullText
      if (parent.subStatus !== 'completed') parent._subStatusText = '回复中...'
    }
    return
  }
    return
  }

  deltaAccum[partID] = (deltaAccum[partID] || '') + delta
  const fullText = deltaAccum[partID]

  // Redirect sub-session deltas to parent task card
  const partType = partTypeByID[partID]
  if (partType === 'reasoning' || partType === 'text') {
  }

  if (!streamingPartId.value || streamingPartId.value !== partID) {
    streamingPartId.value = partID
    const last = messages.value[messages.value.length - 1]
    if (last && last.type === 'message' && last.role === 'assistant' && last.loading) {
      messages.value = messages.value.filter(m => m.id !== last.id)
    }
  }

  // Check if a reasoning block with this partID already exists
  const reasoningMsg = messages.value.find(m => m._partId === partID && m._sse && m.type === 'reasoning')
  if (reasoningMsg) {
    reasoningMsg.content = fullText
    return
  }

  // Check if a text message with this partID already exists
  const textMsg = messages.value.find(m => m._partId === partID && m._sse && m.type === 'message' && m.role === 'assistant')
  if (textMsg) {
    textMsg.content = fullText
    textMsg.typing = true
    textMsg.loading = false
    return
  }

  // Don't create a new message for deltas without a container yet — wait for part.updated
}

function handlePartUpdated(part) {
  if (!part || !part.type) return

  // Skip parts belonging to user messages (echoed input)
  if (part.messageID && currentUserMessageId && part.messageID === currentUserMessageId) return

  delete deltaAccum[part.id]

  // Skip step-start/step-finish/snapshot/patch internal parts
  if (['step-start', 'step-finish', 'snapshot', 'patch'].includes(part.type)) return

  // Track part type for delta routing
  partTypeByID[part.id] = part.type

  const text = part.text || ''
  const isSubSession = part.sessionID && subSessionIds.has(part.sessionID)

  // Sub-session text/reasoning: nest inside parent task card
  if (isSubSession && (part.type === 'text' || part.type === 'reasoning')) {
    const parent = messages.value.find(m => m.type === 'tool_call' && m.subSessionId === part.sessionID)
    if (parent && text) {
      if (parent.subStatus !== 'completed') {
        if (part.type === 'reasoning') {
          parent._subReasoning = (parent._subReasoning || '') + text
          parent._subStatusText = '思考中...'
        } else {
          parent._subText = (parent._subText || '') + text
          parent._subStatusText = '回复中...'
        }
      } else {
        if (part.type === 'reasoning') parent._subReasoning = (parent._subReasoning || '') + text
        else parent._subText = (parent._subText || '') + text
      }
      // If all tools are done and text has arrived, mark as completed
      if (parent._subTools?.length) {
        const allDone = parent._subTools.every(t => t.status === 'completed' || t.status === 'failed')
        if (allDone && parent.subStatus !== 'completed') {
          parent.subStatus = 'completed'
          parent._subStatusText = `已完成 (${countLabel(parent._toolCount || 0, parent._skillCount || 0)})`
        }
      }
    }
    return
  }

  switch (part.type) {
    case 'text': {
      const existing = messages.value.find(m => m._partId === part.id && m._sse && m.type === 'message' && m.role === 'assistant')
      if (existing) {
        existing.content = text
        existing.typing = false
      } else {
        // Create placeholder — deltas will fill it later
        messages.value.push({ id: uid(), _partId: part.id, _sse: true, type: 'message', role: 'assistant', content: text, loading: !text, typing: false })
        scrollToBottom()
      }
      break
    }
    case 'reasoning': {
      const existing = messages.value.find(m => m._partId === part.id && m._sse && m.type === 'reasoning')
      if (existing) {
        existing.content = text
      } else {
        // Create placeholder even with empty text — deltas will fill it
        messages.value.push({ id: uid(), _partId: part.id, _sse: true, type: 'reasoning', content: text, expanded: false })
        scrollToBottom()
      }
      break
    }
    case 'tool': {
      const toolName = part.tool || 'unknown'
      const state = part.state || {}
      const status = state.status || 'running'
      const input = state.input
      const output = state.output
      const metadata = state.metadata || {}
      const subSessionId = metadata.sessionId
      const subOutput = metadata.output
      const isSubSession = part.sessionID && subSessionIds.has(part.sessionID)
      const agentName = isSubSession
        ? (subAgentNames[part.sessionID] || part.sessionID)
        : (metadata.agent || metadata.name || (toolName === 'task' && input?.subagent_type))

      if (isSubSession) {
        // Sub-agent tool: nest inside parent task card
        if (status === 'pending') break
        const parent = messages.value.find(m => m.type === 'tool_call' && m.subSessionId === part.sessionID)
        if (parent) {
          if (parent.subStatus !== 'completed') parent._subStatusText = `调用工具: ${toolName}`
          if (!parent._subTools) parent._subTools = []
          const existing = parent._subTools.find(t => t.tool === toolName && t.status === 'running')
          if (existing) {
            existing.status = status
            if (input !== undefined) existing.input = input
            if (output !== undefined) existing.output = output
          } else {
            const source = commandSourceMap[toolName.toLowerCase()] || 'command'
            if (source === 'skill') parent._skillCount = (parent._skillCount || 0) + 1
            else parent._toolCount = (parent._toolCount || 0) + 1
            parent._subTools.push({
              id: uid(), tool: toolName, status, input, output,
              _expanded: false,
            })
          }
          if (status === 'completed' || status === 'failed') {
            const allDone = parent._subTools?.every(t => t.status === 'completed' || t.status === 'failed')
            if (allDone) {
              const countInfo = countLabel(parent._toolCount || 0, parent._skillCount || 0)
              if (parent._subText) {
                parent.subStatus = 'completed'
                parent._subStatusText = `已完成 (${countInfo})`
              } else {
                parent.subStatus = 'running'
                parent._subStatusText = `等待回复... (${countInfo})`
              }
            }
          }
        }
      } else {
        addToolCallMsg(toolName, status, input, output || subOutput, subSessionId, agentName, false)
        if (subSessionId) {
          subSessionIds.add(subSessionId)
          if (agentName) subAgentNames[subSessionId] = agentName
          if (status === 'completed') {
            const toolMsg = messages.value.find(m => m.type === 'tool_call' && m.subSessionId === subSessionId)
            if (toolMsg && toolMsg._subText) toolMsg.subStatus = 'completed'
          }
        }
      }
      break
    }
  }
}

// --- WebSocket ---

let ws = null
let wsReconnectTimer = null

function connectWs() {
  if (ws && ws.readyState === WebSocket.OPEN) return
  ws = new WebSocket(`ws://127.0.0.1:8000/ws/data`)
  ws.onmessage = (e) => {
    try { renderData(JSON.parse(e.data)) } catch { /* ignore */ }
  }
  ws.onclose = () => { wsReconnectTimer = setTimeout(connectWs, 1000) }
  ws.onerror = () => ws?.close()
}

function disconnectWs() {
  clearTimeout(wsReconnectTimer)
  if (ws) {
    ws.onclose = null; ws.onmessage = null; ws.onerror = null
    ws.close(); ws = null
  }
}

function renderData(data) {
  if (!data || !data.type || !data.data || !data.data.length) return
  if (data.type === 'points') {
    data.data.forEach(item => {
      const loc = item.location
      if (loc?.lng != null && loc?.lat != null) {
        mapContainer.addMarker([loc.lng, loc.lat], { title: item.formatted_address || item.address || '', label: { content: item.formatted_address || item.address || '点位', direction: 'top' } })
      }
    })
    const first = data.data[0]?.location
    if (first) mapContainer.setCenter([first.lng, first.lat], 14)
  } else if (data.type === 'polyline') {
    data.data.forEach((item, i) => {
      if (i === 0 && item.origin && item.destination) {
        if (item.origin.lng != null) mapContainer.addMarker([item.origin.lng, item.origin.lat], { title: item.origin.address || '起点', label: { content: item.origin.address || '起点', direction: 'top' } })
        if (item.destination.lng != null) mapContainer.addMarker([item.destination.lng, item.destination.lat], { title: item.destination.address || '终点', label: { content: item.destination.address || '终点', direction: 'top' } })
        return
      }
      const coords = (item.polyline || []).map(p => [p.lng, p.lat])
      if (coords.length > 0) mapContainer.addPolyline(coords, { strokeColor: '#AA00FF', strokeWeight: 5 })
    })
    const meta = data.data[0]
    if (meta?.origin && meta?.destination) mapContainer.setCenter([(meta.origin.lng + meta.destination.lng) / 2, (meta.origin.lat + meta.destination.lat) / 2], 12)
  } else if (data.type === 'distence') {
    data.data.forEach(item => {
      if (item.origin) mapContainer.addMarker([item.origin.lng, item.origin.lat], { title: item.origin.address || '起点', label: { content: item.origin.address || '起点', direction: 'top' } })
      if (item.destination) mapContainer.addMarker([item.destination.lng, item.destination.lat], { title: item.destination.address || '终点', label: { content: item.destination.address || '终点', direction: 'top' } })
      if (item.origin && item.destination) mapContainer.addPolyline([[item.origin.lng, item.origin.lat], [item.destination.lng, item.destination.lat]], { strokeColor: '#FF6B6B', strokeWeight: 3, strokeStyle: 'dashed' })
    })
    const item = data.data[0]
    if (item?.origin && item?.destination) mapContainer.setCenter([(item.origin.lng + item.destination.lng) / 2, (item.origin.lat + item.destination.lat) / 2], 12)
  }
}

// --- Send & receive ---

async function abortSession() {
  if (!currentSessionId.value) return
  try { await fetch(`${SERVER_URL}/session/${currentSessionId.value}/abort`, { method: 'POST' }) } catch {}
  sessionBusy.value = false
  streamingPartId.value = null
  for (const m of messages.value) {
    if (m.typing) m.typing = false
    if (m.type === 'tool_call') {
      if (m.status === 'running') m.status = 'cancelled'
      if (m.subStatus === 'running') {
        m.subStatus = 'cancelled'
        m._subStatusText = '已取消'
        if (m._subTools) {
          for (const st of m._subTools) {
            if (st.status === 'running') st.status = 'cancelled'
          }
        }
      }
    }
  }
}

async function handleSend() {
  const text = inputText.value
  if (sessionBusy.value || !text.trim()) return

  mapContainer?.clearMarkers?.()
  mapContainer?.clearPolylines?.()
  const points = mapContainer?.getUserPoints?.() || []
  userPointsCount.value = points.length

  let fullText = text
  if (points.length > 0) {
    fullText = `[地图标注点]\n${points.map(p => `${p.label} (${p.lng}, ${p.lat})`).join('\n')}\n\n[用户问题]\n${text}`
  }

  if (!currentSessionId.value) {
    const created = await createSession()
    if (!created) return
  }

  addMessage('user', fullText, { points: points.length > 0 ? points : undefined, userText: text })
  inputText.value = ''
  if (textareaRef.value) textareaRef.value.style.height = 'auto'

  const loadingMsg = { id: uid(), type: 'message', role: 'assistant', content: '', loading: true, typing: false }
  messages.value.push(loadingMsg)
  scrollToBottom()

  sessionBusy.value = true
  streamingPartId.value = null
  currentUserMessageId = null
  subSessionIds.clear()

  try {
    const response = await fetch(`${SERVER_URL}/session/${currentSessionId.value}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent: 'gis-orchestrator',
        model: selectedModel.value ? (() => {
          const m = modelOptions.value.find(o => o.value === selectedModel.value)
          return m ? { providerID: m.providerID, modelID: m.value } : undefined
        })() : undefined,
        parts: [{ type: 'text', text: fullText }]
      })
    })

    if (response.ok) {
      const result = await response.json()
      const rawParts = Array.isArray(result) ? result : (result.parts || [])
      const hasText = rawParts.some(p => p.type === 'text' && p.text)
      if (hasText) {
        messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
      }
      applyFinalResponse(rawParts, fullText)
      if (!hasText) {
        // Text will arrive via SSE — keep loading message, let session.status:idle handle cleanup
      }
    } else {
      messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
      const errorText = await response.text()
      addMessage('assistant', `请求失败: ${errorText}`)
      sessionBusy.value = false
    }
  } catch (error) {
    messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
    addMessage('assistant', `请求失败: ${error.message}`)
    sessionBusy.value = false
  }
}

function applyFinalResponse(rawParts, userText) {
  // SSE already streamed all content — POST response only updates tool status & cleans up
  for (const part of rawParts) {
    if (part.type === 'text') {
      // Text is already handled by SSE — skip
      continue
    }
    if (part.type === 'tool') {
      const toolName = part.tool || 'unknown'
      const status = part.state?.status || 'completed'
      const input = part.state?.input
      const output = part.state?.output
      const metadata = part.state?.metadata
      const subSessionId = metadata?.sessionId
      const subOutput = metadata?.output
      const agentName = metadata?.agent || metadata?.name || (toolName === 'task' && input?.subagent_type)

      addToolCallMsg(toolName, status, input, output || subOutput, subSessionId, agentName)
      if (subSessionId) {
        subSessionIds.add(subSessionId)
        if (agentName) subAgentNames[subSessionId] = agentName
        const toolMsg = messages.value.find(m => m.type === 'tool_call' && m.subSessionId === subSessionId)
        if (toolMsg) {
          if (status === 'completed' && toolMsg._subText) toolMsg.subStatus = 'completed'
          else if (status !== 'completed') toolMsg.subStatus = 'running'
        }
      }
    }
  }

  for (const m of messages.value) {
    if (m.typing) m.typing = false
  }
}



function init() {
  connectWs()
  connectEventSource()
  checkServerHealth().then(ok => {
    if (ok) { fetchModels(); fetchCommands(); createSession() }
  })
}

init()

onUnmounted(() => {
  disconnectWs()
  disconnectEventSource()
})
</script>

<style scoped>
/* === Panel === */
.chat-panel {
  position: fixed;
  left: 20px;
  top: 20px;
  bottom: 20px;
  width: 450px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.06);
  z-index: 10;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.04);
}
.resize-handle {
  position: absolute;
  right: -2px; top: 0; bottom: 0;
  width: 8px;
  cursor: col-resize;
  z-index: 20;
}

/* === Header === */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #fafbfc 0%, #f6f8fa 100%);
}
.chat-header h3 {
  font-size: 14px;
  font-weight: 700;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.3px;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.add-point-wrapper {
  position: relative;
  display: inline-flex;
}
.icon-btn {
  width: 32px; height: 32px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  color: #555;
  transition: all 0.2s ease;
  padding: 0;
}
.icon-btn:hover {
  background: #e4e4e4;
  transform: scale(1.05);
}
.icon-btn:active {
  transform: scale(0.95);
}
.icon-btn.active {
  background: linear-gradient(135deg, #1890ff, #096dd9) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.4);
}
.new-session-btn {
  background: #f0f0f0 !important;
}
.new-session-btn:hover {
  background: #e4e4e4 !important;
}
.point-badge {
  position: absolute;
  top: -4px; right: -4px;
  min-width: 16px; height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: #f5222d;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  line-height: 16px;
  text-align: center;
  pointer-events: none;
}

/* === Messages === */
.chat-messages {
  flex: 1;
  overflow: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
  background: #fafbfc;
}
.chat-messages > * {
  flex-shrink: 0;
}

.msg-row {
  display: flex;
  animation: msgFadeIn 0.2s ease;
}
@keyframes msgFadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
.msg-row.assistant {
  justify-content: flex-start;
}
.msg-row.user {
  justify-content: flex-end;
}
.msg-row.system {
  justify-content: center;
}

/* === Bubbles === */
.bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.55;
  word-break: break-word;
}
.bubble.assistant {
  background: #fff;
  color: #1a1a2e;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.bubble.user {
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.25);
}
.bubble.user .points-card {
  --text-color: #1a5cc8;
  --bg-color: #f0f5ff;
}
.bubble.user .user-text {
  color: #fff;
}
.bubble[data-loading] {
  display: flex;
  align-items: center;
  min-height: 36px;
  background: #fff;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
}
.loading-indicator .dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #bbb;
  animation: dotBounce 1.4s infinite ease-in-out;
}
.loading-indicator .dot:nth-child(1) { animation-delay: 0s; }
.loading-indicator .dot:nth-child(2) { animation-delay: 0.16s; }
.loading-indicator .dot:nth-child(3) { animation-delay: 0.32s; }
@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.dot-pulse {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #999;
  animation: dotPulse 1.4s infinite ease-in-out;
}
@keyframes dotPulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}

/* === Markdown content === */
.md-content {
  font-size: 13px;
  line-height: 1.6;
}
.md-content :deep(p) { margin: 0 0 8px; }
.md-content :deep(p:last-child) { margin-bottom: 0; }
.md-content :deep(h1) { font-size: 18px; margin: 14px 0 8px; font-weight: 700; color: #1a1a2e; }
.md-content :deep(h2) { font-size: 16px; margin: 12px 0 6px; font-weight: 700; color: #1a1a2e; }
.md-content :deep(h3) { font-size: 14px; margin: 10px 0 4px; font-weight: 600; color: #1a1a2e; }
.md-content :deep(h4) { font-size: 13px; margin: 8px 0 4px; font-weight: 600; color: #333; }
.md-content :deep(code) {
  font-size: 12px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
  background: rgba(0,0,0,0.06);
  padding: 2px 5px;
  border-radius: 4px;
  color: #e74c3c;
}
.md-content :deep(pre) {
  background: #1a1a2e;
  border-radius: 8px;
  padding: 12px 14px;
  overflow-x: auto;
  margin: 10px 0;
}
.md-content :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #e8e8e8;
}
.md-content :deep(ul), .md-content :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}
.md-content :deep(li) { margin: 3px 0; }
.md-content :deep(a) { color: #1890ff; text-decoration: none; }
.md-content :deep(a:hover) { text-decoration: underline; }
.md-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 12px;
  border-radius: 8px;
  overflow: hidden;
}
.md-content :deep(th), .md-content :deep(td) {
  border: 1px solid #e8e8e8;
  padding: 8px 12px;
  text-align: left;
}
.md-content :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
  color: #333;
}
.md-content :deep(tbody tr:nth-child(even)) {
  background: #fafbfc;
}
.md-content :deep(hr) {
  border: none;
  border-top: 1px solid #e8e8e8;
  margin: 14px 0;
}
.md-content :deep(blockquote) {
  margin: 8px 0;
  padding: 6px 14px;
  border-left: 3px solid #d0d5dd;
  color: #666;
  font-size: 12px;
  background: #f8f9fa;
  border-radius: 0 6px 6px 0;
}
.md-content :deep(strong) { font-weight: 600; color: #1a1a2e; }
.md-content :deep(del) { text-decoration: line-through; color: #999; }
.md-content :deep(br) { content: ''; display: block; margin: 4px 0; }

/* Typing cursor */
.md-content[data-typing]::after {
  content: '|';
  display: inline;
  animation: cursorBlink 0.8s step-end infinite;
  color: #1890ff;
  font-weight: 500;
}
@keyframes cursorBlink {
  50% { opacity: 0; }
}

.user-text {
  font-size: 13px;
  line-height: 1.5;
}

/* === System message === */
.system-msg {
  width: 100%;
  text-align: center;
  font-size: 11px;
  color: #999;
  padding: 4px 0;
}

/* === Points card === */
.points-card {
  background: linear-gradient(135deg, #f0f5ff, #e8f0fe);
  border: 1px solid #d6e4ff;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 8px;
}
.points-card-header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  background: rgba(24, 144, 255, 0.08);
  font-size: 11px;
  font-weight: 600;
  color: #1a5cc8;
  border-bottom: 1px solid #d6e4ff;
}
.points-count {
  margin-left: auto;
  background: #1890ff;
  color: #fff;
  font-size: 9px;
  font-weight: 600;
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: 9px;
  padding: 0 5px;
}
.points-card-body { padding: 6px 10px; }
.point-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  font-size: 11px;
}
.point-item + .point-item { border-top: 1px solid #e6f0ff; }
.point-label {
  width: 22px; height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(24, 144, 255, 0.3);
}
.point-coords {
  color: #666;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 10px;
}

/* === Thinking block === */
.thinking-block {
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.thinking-block summary {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 14px;
  font-size: 12px;
  font-weight: 600;
  color: #555;
  cursor: pointer;
  user-select: none;
  background: #fafbfc;
  transition: background 0.15s;
}
.thinking-block summary:hover {
  background: #f5f7fa;
}
.thinking-block summary .chevron {
  margin-left: auto;
  transition: transform 0.2s;
  color: #bbb;
}
.thinking-block[open] summary .chevron {
  transform: rotate(180deg);
}
.thinking-block[open] summary {
  border-bottom: 1px solid #f0f0f0;
}
.thinking-content {
  padding: 0 14px 14px;
  font-size: 12px;
  color: #666;
  line-height: 1.6;
}
.thinking-content :deep(p) { font-size: 12px; }

/* === Thought chain === */
.thought-chain {
  padding: 10px 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.chain-step {
  display: flex;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #f8f9fa;
  font-size: 12px;
  transition: background 0.15s;
}
.chain-step:hover {
  background: #f0f2f5;
}
.chain-step-indicator {
  flex-shrink: 0;
  width: 20px;
  display: flex;
  justify-content: center;
  padding-top: 2px;
}
.step-icon {
  width: 16px; height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
}
.step-icon.completed { background: #52c41a; color: #fff; }
.step-icon.error { background: #ff4d4f; color: #fff; }
.step-icon.active {
  background: #1890ff;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.2);
  animation: pulse 1.5s infinite;
}
.step-icon.pending {
  background: #d9d9d9;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.chain-step-body { flex: 1; }
.chain-step-title { font-weight: 600; color: #333; }
.chain-step-content { color: #888; font-size: 11px; margin-top: 3px; }

/* === Tool call card === */
.tool-call-card {
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.tool-call-card.completed { border-left: 3px solid #52c41a; }
.tool-call-card.failed { border-left: 3px solid #ff4d4f; }
.tool-call-card.running { border-left: 3px solid #1890ff; }
.tool-call-card.cancelled { border-left: 3px solid #d9d9d9; }

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 12px;
  font-size: 11px;
  color: #555;
  background: #fafbfc;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.15s;
}
.tool-agent-badge {
  font-size: 10px;
  font-weight: 600;
  color: var(--color, #6366f1);
  background: color-mix(in srgb, var(--color, #6366f1) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--color, #6366f1) 20%, transparent);
  border-radius: 4px;
  padding: 1px 7px;
  white-space: nowrap;
}
.tool-call-name {
  font-weight: 600;
  color: #333;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 11px;
}
.tool-call-status {
  margin-left: auto;
  font-size: 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #888;
}
.tool-call-status.completed { color: #52c41a; }
.tool-call-status.failed { color: #ff4d4f; }
.tool-call-status.running { color: #1890ff; }
.tool-call-status.cancelled { color: #999; }

.sub-agent-indicator {
  font-size: 10px;
  display: flex;
  align-items: center;
  gap: 3px;
  color: #888;
  white-space: nowrap;
}
.sub-agent-indicator.running {
  color: #1890ff;
}
.sub-agent-spinner {
  width: 8px;
  height: 8px;
  border: 1.5px solid #1890ff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  display: inline-block;
}
.status-dot.running { background: #1890ff; animation: pulse 1.5s infinite; }
.status-dot.completed { background: #52c41a; }
.status-dot.failed { background: #ff4d4f; }
.status-dot.cancelled { background: #d9d9d9; }

.tool-toggle {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  padding: 3px 6px;
  border-radius: 5px;
  transition: all 0.15s;
}
.tool-toggle:hover { background: #e8e8e8; color: #555; }

.tool-call-body {
  padding: 10px 12px;
  background: #fafbfc;
}
.tool-section { margin-bottom: 8px; }
.tool-section:last-child { margin-bottom: 0; }
.tool-section-label {
  font-size: 10px;
  font-weight: 600;
  color: #999;
  margin-bottom: 5px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.tool-code {
  font-size: 10px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 8px 10px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  color: #444;
  line-height: 1.5;
  max-height: 150px;
  overflow-y: auto;
}
.sub-tools {
  margin-top: 10px;
  border-top: 1px solid #e8e8e8;
  padding-top: 8px;
}
.sub-tool-item {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  margin-top: 6px;
  overflow: hidden;
  background: #fafbfc;
}
.sub-tool-item.completed { border-left: 2px solid #52c41a; }
.sub-tool-item.failed { border-left: 2px solid #ff4d4f; }
.sub-tool-item.running { border-left: 2px solid #1890ff; }
.sub-tool-header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 8px;
  font-size: 10px;
  color: #555;
  background: #f5f7fa;
}
.sub-tool-name {
  font-weight: 600;
  color: #333;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 10px;
}
.sub-tool-body {
  padding: 6px 8px;
}
.sub-agent-response {
  margin-top: 8px;
}
.sub-reasoning {
  font-size: 11px;
  color: #666;
  background: #f5f7fa;
  border-radius: 6px;
  padding: 8px 10px;
  line-height: 1.5;
  white-space: pre-wrap;
}
.sub-text {
  font-size: 12px;
  line-height: 1.5;
  background: #f8faff;
  border: 1px solid #e0e7ff;
  border-radius: 6px;
  padding: 8px 10px;
}

.sub-agent-bar {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #f0f5ff, #e8f0fe);
  border-top: 1px solid #d6e4ff;
  font-size: 10px;
  color: #1a5cc8;
}
.sub-agent-status {
  margin-left: auto;
  font-size: 10px;
  color: #888;
}
.sub-agent-status.active { color: #1890ff; }

/* === Input area === */
.chat-input-area {
  padding: 8px 14px 14px;
  border-top: 1px solid #f0f0f0;
  background: #fff;
}
.input-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
.model-select-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.model-icon { color: #999; flex-shrink: 0; }
.model-select {
  appearance: none;
  -webkit-appearance: none;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 5px 24px 5px 10px;
  font-size: 12px;
  color: #555;
  background: #fafbfc url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E") no-repeat right 8px center;
  cursor: pointer;
  outline: none;
  min-width: 130px;
  max-width: 200px;
  transition: all 0.2s;
}
.model-select:hover { border-color: #d0d0d0; background-color: #fff; }
.model-select:focus { border-color: #1890ff; box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.1); background-color: #fff; }

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}
.chat-textarea {
  flex: 1;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 9px 14px;
  font-size: 13px;
  font-family: inherit;
  resize: none;
  outline: none;
  min-height: 38px;
  max-height: 120px;
  line-height: 1.45;
  transition: all 0.2s;
  background: #fafbfc;
}
.chat-textarea:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.08);
  background: #fff;
}
.chat-textarea:disabled {
  background: #f5f5f5;
  color: #999;
  border-color: #e8e8e8;
}
.send-btn, .stop-btn {
  width: 38px; height: 38px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s ease;
}
.send-btn {
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}
.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.4);
}
.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}
.send-btn:disabled { background: #d9d9d9; box-shadow: none; cursor: not-allowed; }
.stop-btn {
  background: #ff4d4f;
  color: #fff;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.3);
}
.stop-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.4);
}
</style>
