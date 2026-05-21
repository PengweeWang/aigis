<template>
  <div class="chat-panel" :style="{ width: panelWidth + 'px' }">
    <div class="resize-handle" @mousedown="startResize"></div>
    <div class="chat-header">
      <h3>GIS Chat</h3>
      <div class="header-actions">
        <div class="add-point-wrapper">
          <el-tooltip :content="pointAddMode ? '关闭标注模式 (点击标记删除)' : '开启标注模式'" placement="bottom">
            <el-button class="add-point-btn" :class="{ active: pointAddMode }" :size="'small'" circle @click="togglePointAddMode">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" :stroke="pointAddMode ? '#fff' : 'currentColor'" stroke-width="2">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                <circle cx="12" cy="9" r="2.5"/>
              </svg>
            </el-button>
          </el-tooltip>
          <span v-if="userPointsCount > 0" class="point-badge">{{ userPointsCount }}</span>
        </div>
        <el-tooltip content="新建会话" placement="bottom">
          <el-button class="new-session-btn" :size="'small'" circle @click="createNewSession">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </el-button>
        </el-tooltip>
      </div>
    </div>

    <ElABubbleList ref="bubbleListRef" class="chat-messages">
      <template v-for="msg in messages" :key="msg.id">
        <ElABubble
          v-if="msg.type === 'message'"
          :placement="msg.role === 'user' ? 'end' : 'start'"
          :content="msg.content"
          :typing="msg.role === 'assistant' && msg.typing"
          :loading="msg.loading"
          :is-markdown="msg.role === 'assistant'"
        >
          <template v-if="msg.role === 'user' && msg.points" #default>
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
        </ElABubble>
        <ElAThinking
          v-else-if="msg.type === 'reasoning'"
          v-model="msg.expanded"
          title="思考过程"
        >
          <ElAMarkdown :content="msg.content" />
        </ElAThinking>
      </template>
    </ElABubbleList>

    <div class="chat-input-area">
      <div class="input-toolbar">
        <div class="model-select-wrapper">
          <svg class="model-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
          </svg>
          <select v-model="selectedModel" class="model-select" @change="handleModelChange">
            <option v-for="m in modelOptions" :key="m.value" :value="m.value">
              {{ m.label }}
            </option>
          </select>
        </div>
      </div>
      <ElASender
        v-model="inputText"
        placeholder="请输入您的问题..."
        @send="handleSend"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, inject, onUnmounted } from 'vue'
import { ElABubble, ElABubbleList, ElASender, ElAThinking, ElAMarkdown } from 'element-ai-vue'

const SERVER_URL = 'http://127.0.0.1:4096'
const DATA_SERVER = 'http://127.0.0.1:8000'
const bubbleListRef = ref(null)
const mapContainer = inject('mapContainer')

const panelWidth = ref(450)
const resizing = ref(false)

const messages = ref([])
const inputText = ref('')
const currentSessionId = ref(null)
const modelOptions = ref([])
const selectedModel = ref('')
const pointAddMode = ref(false)
const userPointsCount = ref(0)

// SSE streaming state
let eventSource = null
let eventReconnectTimer = null
const streamState = ref({
  assistantMessageId: null,
  partTexts: {},
  isStreaming: false,
})

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

async function checkServerHealth() {
  try {
    const response = await fetch(`${SERVER_URL}/global/health`)
    if (response.ok) {
      const data = await response.json()
      addSystemMessage(`已连接至GIS智能体，版本: ${data.version}`)
      return true
    }
  } catch (error) {
    addSystemMessage('无法连接到OpenCode服务器，请确保已运行 opencode serve')
  }
  return false
}

async function createSession() {
  try {
    const response = await fetch(`${SERVER_URL}/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
    if (response.ok) {
      const session = await response.json()
      currentSessionId.value = session.id
      return true
    }
  } catch (error) {
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
  await createSession()
  addSystemMessage('已创建新会话')
}

function addSystemMessage(text) {
  messages.value.push({
    id: Date.now().toString() + '-system',
    type: 'system',
    content: text
  })
  scrollToBottom()
}

function addMessage(role, content, extra = {}) {
  messages.value.push({
    id: Date.now().toString() + '-' + role,
    type: 'message',
    role,
    content,
    ...extra
  })
  scrollToBottom()
}

function addReasoningMessage(text) {
  messages.value.push({
    id: Date.now().toString() + '-reasoning',
    type: 'reasoning',
    content: text,
    expanded: false
  })
  scrollToBottom()
}

async function fetchModels() {
  try {
    const response = await fetch(`${SERVER_URL}/config/providers`)
    if (!response.ok) return
    const data = await response.json()
    const options = []
    for (const provider of data.providers || []) {
      for (const model of Object.values(provider.models || {})) {
        options.push({
          value: model.id,
          providerID: model.providerID,
          label: `${provider.name} - ${model.name || model.id}`,
        })
      }
    }
    if (options.length === 0) return
    modelOptions.value = options
    selectedModel.value = options.find(o => o.value === 'minimax-m2.5-free')?.value
      || options[0].value
  } catch {
    // ignore
  }
}

function handleModelChange() {
  // model selection changed
}

// SSE event stream for streaming AI responses
function connectEventStream() {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  clearTimeout(eventReconnectTimer)

  eventSource = new EventSource('/global/event')

  eventSource.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data)
      handleSseEvent(msg)
    } catch { /* ignore */ }
  }

  eventSource.onerror = () => {
    eventSource?.close()
    eventSource = null
    eventReconnectTimer = setTimeout(connectEventStream, 3000)
  }
}

function handleSseEvent(msg) {
  const payload = msg.payload
  if (!payload?.properties) return

  const props = payload.properties
  if (props.sessionID !== currentSessionId.value) return

  switch (payload.type) {
    case 'message.updated':
      if (props.info?.role === 'assistant') {
        // Remove loading placeholder, start streaming
        messages.value = messages.value.filter(m => !m.loading)
        streamState.value = {
          assistantMessageId: props.info.id,
          partTexts: {},
          isStreaming: true,
        }
        // Check if message already exists (e.g., from SSE reconnect)
        if (!messages.value.find(m => m.id === props.info.id)) {
          messages.value.push({
            id: props.info.id,
            type: 'message',
            role: 'assistant',
            content: '',
            typing: true,
            loading: false,
          })
        }
        scrollToBottom()
      }
      break

    case 'message.part.updated': {
      const part = props.part
      if (!part) break

      if (part.type === 'reasoning' && part.text) {
        addReasoningMessage(part.text)
      } else if (part.type === 'text' && part.messageID === streamState.value.assistantMessageId) {
        if (part.text) {
          streamState.value.partTexts[part.id] = part.text
          updateStreamingContent()
        }
      } else if (part.type === 'step-finish') {
        finalizeStreamingMessage(part.messageID)
      }
      break
    }

    case 'message.part.delta': {
      const { messageID, partID, delta } = props
      if (messageID === streamState.value.assistantMessageId && delta) {
        streamState.value.partTexts[partID] = (streamState.value.partTexts[partID] || '') + delta
        updateStreamingContent()
      }
      break
    }
  }
}

function updateStreamingContent() {
  const text = Object.values(streamState.value.partTexts).join('')
  const msg = messages.value.find(m => m.id === streamState.value.assistantMessageId)
  if (msg) {
    msg.content = text
    scrollToBottom()
  }
}

function finalizeStreamingMessage(messageID) {
  const targetId = messageID || streamState.value.assistantMessageId
  const msg = messages.value.find(m => m.id === targetId)
  if (msg) {
    msg.typing = false
  } else if (targetId && streamState.value.isStreaming) {
    // No streaming message was created (e.g. no text parts), remove loading
    messages.value = messages.value.filter(m => !m.loading)
    if (!messages.value.some(m => m.role === 'assistant' && !m.loading)) {
      addMessage('assistant', '回答内容为空')
    }
  }
  streamState.value.isStreaming = false
  streamState.value.assistantMessageId = null
  streamState.value.partTexts = {}
}

function togglePointAddMode() {
  pointAddMode.value = !pointAddMode.value
  if (pointAddMode.value) {
    mapContainer?.enableAddMode?.()
  } else {
    mapContainer?.disableAddMode?.()
  }
}

function updateUserPointsCount() {
  const points = mapContainer?.getUserPoints?.() || []
  userPointsCount.value = points.length
}

function scrollToBottom() {
  nextTick(() => {
    if (bubbleListRef.value?.scrollToBottom) {
      bubbleListRef.value.scrollToBottom()
    }
  })
}

let ws = null
let wsReconnectTimer = null

function connectWs() {
  if (ws && ws.readyState === WebSocket.OPEN) return
  ws = new WebSocket(`ws://127.0.0.1:8000/ws/data`)
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.type) renderData(data)
    } catch { /* ignore */ }
  }
  ws.onclose = () => {
    wsReconnectTimer = setTimeout(connectWs, 1000)
  }
  ws.onerror = () => ws?.close()
}

function disconnectWs() {
  clearTimeout(wsReconnectTimer)
  if (ws) {
    ws.onclose = null
    ws.onmessage = null
    ws.onerror = null
    ws.close()
    ws = null
  }
}

function renderData(data) {
  if (!data || !data.type || !data.data || data.data.length === 0) return

  // Use requestAnimationFrame to avoid blocking the main thread
  requestAnimationFrame(() => {
    if (data.type === 'points') {
      data.data.forEach(item => {
      const loc = item.location
      if (loc && loc.lng != null && loc.lat != null) {
        const title = item.formatted_address || item.address || ''
        mapContainer.addMarker([loc.lng, loc.lat], {
          title,
          label: { content: title || '点位', direction: 'top' },
        })
      }
    })
    const first = data.data[0]?.location
    if (first) mapContainer.setCenter([first.lng, first.lat], 14)
  } else if (data.type === 'polyline') {
    data.data.forEach((item, index) => {
      if (index === 0 && item.origin && item.destination) {
        if (item.origin.lng != null && item.origin.lat != null) {
          mapContainer.addMarker([item.origin.lng, item.origin.lat], {
            title: item.origin.address || '起点',
            label: { content: item.origin.address || '起点', direction: 'top' },
          })
        }
        if (item.destination.lng != null && item.destination.lat != null) {
          mapContainer.addMarker([item.destination.lng, item.destination.lat], {
            title: item.destination.address || '终点',
            label: { content: item.destination.address || '终点', direction: 'top' },
          })
        }
        return
      }
      const coords = (item.polyline || []).map(p => [p.lng, p.lat])
      if (coords.length > 0) {
        mapContainer.addPolyline(coords, { strokeColor: '#AA00FF', strokeWeight: 5 })
      }
    })
    const meta = data.data[0]
    if (meta?.origin && meta?.destination) {
      const cx = (meta.origin.lng + meta.destination.lng) / 2
      const cy = (meta.origin.lat + meta.destination.lat) / 2
      mapContainer.setCenter([cx, cy], 12)
    }
  } else if (data.type === 'distence') {
    data.data.forEach(item => {
      if (item.origin) {
        mapContainer.addMarker([item.origin.lng, item.origin.lat], {
          title: item.origin.address || '起点',
          label: { content: item.origin.address || '起点', direction: 'top' },
        })
      }
      if (item.destination) {
        mapContainer.addMarker([item.destination.lng, item.destination.lat], {
          title: item.destination.address || '终点',
          label: { content: item.destination.address || '终点', direction: 'top' },
        })
      }
      if (item.origin && item.destination) {
        mapContainer.addPolyline(
          [[item.origin.lng, item.origin.lat], [item.destination.lng, item.destination.lat]],
          { strokeColor: '#FF6B6B', strokeWeight: 3, strokeStyle: 'dashed' },
        )
      }
    })
    const item = data.data[0]
    if (item?.origin && item?.destination) {
      const cx = (item.origin.lng + item.destination.lng) / 2
      const cy = (item.origin.lat + item.destination.lat) / 2
      mapContainer.setCenter([cx, cy], 12)
    }
  }
  })
}

async function handleSend(text) {
  mapContainer?.clearMarkers?.()
  mapContainer?.clearPolylines?.()
  const points = mapContainer?.getUserPoints?.() || []
  userPointsCount.value = points.length
  let fullText = text
  if (points.length > 0) {
    const pointsDesc = points.map(p =>
      `${p.label} (${p.lng}, ${p.lat})`
    ).join('\n')
    fullText = `[地图标注点]\n${pointsDesc}\n\n[用户问题]\n${text}`
  }

  if (!currentSessionId.value) {
    const created = await createSession()
    if (!created) return
  }

  addMessage('user', fullText, {
    points: points.length > 0 ? points : undefined,
    userText: text,
  })
  inputText.value = ''

  // Add loading placeholder (will be replaced by SSE streaming)
  const loadingMsg = {
    id: Date.now().toString() + '-loading',
    type: 'message',
    role: 'assistant',
    content: '',
    loading: true,
    typing: false
  }
  messages.value.push(loadingMsg)
  scrollToBottom()

  // Fire POST — SSE handles streaming UI updates
  fetch(`${SERVER_URL}/session/${currentSessionId.value}/message`, {
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
  }).then(async (response) => {
    if (!response.ok) {
      // SSE didn't stream anything, clean up and show error
      const stillLoading = messages.value.some(m => m.id === loadingMsg.id)
      if (stillLoading) {
        messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
        const errorText = await response.text()
        addMessage('assistant', `请求失败: ${errorText}`)
      }
    }
  }).catch((error) => {
    const stillLoading = messages.value.some(m => m.id === loadingMsg.id)
    if (stillLoading) {
      messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
      addMessage('assistant', `请求失败: ${error.message}`)
    }
  })
}

function renderResponseParts(parts) {
  updateUserPointsCount()
  let reasoningText = ''
  let answerText = ''

  for (const part of parts) {
    if (part.type === 'reasoning') {
      reasoningText += part.text
    } else if (part.type === 'text') {
      answerText += part.text
    }
  }

  if (reasoningText) {
    addReasoningMessage(reasoningText)
  }
  if (answerText) {
    addMessage('assistant', answerText)
  }
  if (!reasoningText && !answerText) {
    addMessage('assistant', '回答内容为空')
  }
}

function testMapFunctions() {
  console.log('[MapTest] 开始测试地图功能')
  if (!mapContainer) {
    console.warn('[MapTest] mapContainer 未找到，请检查 provide/inject')
    return
  }
  console.log('[MapTest] mapContainer 已获取:', mapContainer)
  setTimeout(() => {
    console.log('[MapTest] 执行 setCenter([116.40, 39.91], 13)')
    mapContainer.setCenter([116.40, 39.91], 13)
    console.log('[MapTest] 执行 addMarker([116.40, 39.91])')
    mapContainer.addMarker([116.40, 39.91], {
      title: '测试标记',
      label: { content: '测试点', direction: 'top' },
    })
    console.log('[MapTest] 执行 addPolyline([[116.39,39.90], [116.40,39.91], [116.41,39.90]])')
    mapContainer.addPolyline([
      [116.39, 39.90],
      [116.40, 39.91],
      [116.41, 39.90],
    ], {
      strokeColor: '#FF0000',
      strokeWeight: 4,
    })
    console.log('[MapTest] 地图功能测试完成')
  }, 2000)
}

async function init() {
  connectWs()
  connectEventStream()
  const connected = await checkServerHealth()
  if (connected) {
    await fetchModels()
    await createSession()
    // testMapFunctions()
  }
}

init()

onUnmounted(() => {
  disconnectWs()
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  clearTimeout(eventReconnectTimer)
})
</script>

<style scoped>
.chat-panel {
  position: fixed;
  left: 20px;
  top: 20px;
  bottom: 20px;
  width: 450px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 10;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.chat-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

:deep(.el-ai-bubble) {
  margin-bottom: 8px;
  font-size: 12px;
}

:deep(.el-ai-bubble:last-child) {
  margin-bottom: 0;
}

:deep(.el-ai-bubble .el-ai-markdown) {
  font-size: 12px;
  line-height: 1.6;
}

:deep(.el-ai-bubble .el-ai-markdown p),
:deep(.el-ai-bubble .el-ai-markdown li) {
  font-size: 12px;
  line-height: 1.6;
}

:deep(.el-ai-bubble .el-ai-markdown pre) {
  font-size: 11px;
}

:deep(.el-ai-bubble .el-ai-markdown code) {
  font-size: 11px;
}

:deep(.el-ai-bubble .el-ai-markdown h1) { font-size: 16px; }
:deep(.el-ai-bubble .el-ai-markdown h2) { font-size: 14px; }
:deep(.el-ai-bubble .el-ai-markdown h3) { font-size: 13px; }
:deep(.el-ai-bubble .el-ai-markdown h4) { font-size: 12px; }

:deep(.el-ai-thinking) {
  margin-bottom: 8px;
}

.chat-input-area {
  padding: 6px 12px 12px;
  border-top: 1px solid #eee;
  background: #f8f9fa;
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
  position: relative;
}

.model-icon {
  color: #666;
  flex-shrink: 0;
}

.model-select {
  appearance: none;
  -webkit-appearance: none;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 5px 24px 5px 10px;
  font-size: 12px;
  color: #444;
  background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E") no-repeat right 8px center;
  cursor: pointer;
  outline: none;
  min-width: 140px;
  max-width: 200px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.model-select:hover {
  border-color: #b0b0b0;
}

.model-select:focus {
  border-color: #909399;
  box-shadow: 0 0 0 2px rgba(144, 147, 153, 0.15);
}

.resize-handle {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 5px;
  cursor: col-resize;
  z-index: 20;
}

.new-session-btn {
  background: radial-gradient(circle at center, #b0b0b0 0%, #d8d8d8 70%, #e8e8e8 100%) !important;
  color: #666 !important;
  border: none !important;
  border-radius: 50% !important;
  width: 32px !important;
  min-width: 32px !important;
  height: 32px !important;
  min-height: 32px !important;
  padding: 0 !important;
  margin: 0 !important;
  line-height: 32px !important;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.new-session-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.add-point-wrapper {
  position: relative;
  display: inline-flex;
}

.add-point-btn {
  background: linear-gradient(135deg, #e8e8e8, #d0d0d0) !important;
  color: #555 !important;
  border: none !important;
  border-radius: 50% !important;
  width: 32px !important;
  min-width: 32px !important;
  height: 32px !important;
  min-height: 32px !important;
  padding: 0 !important;
  margin: 0 !important;
  line-height: 32px !important;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.add-point-btn.active {
  background: linear-gradient(135deg, #1890ff, #096dd9) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.4);
}

.point-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 16px;
  height: 16px;
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

.points-card {
  background: #f0f5ff;
  border: 1px solid #d6e4ff;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 8px;
}

.points-card-header {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #e6f0ff;
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
  min-width: 16px;
  height: 16px;
  line-height: 16px;
  text-align: center;
  border-radius: 8px;
  padding: 0 4px;
}

.points-card-body {
  padding: 4px 8px;
}

.point-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 0;
  font-size: 11px;
}

.point-item + .point-item {
  border-top: 1px solid #e6f0ff;
}

.point-label {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #1890ff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}

.point-coords {
  color: #666;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 10px;
}

.user-text {
  font-size: 12px;
  line-height: 1.5;
  color: #333;
  word-break: break-word;
}
</style>