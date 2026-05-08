<template>
  <div class="chat-panel">
    <div class="chat-header">
      <h3>GIS Chat</h3>
      <el-tooltip content="新建会话" placement="bottom">
        <el-button class="new-session-btn" :size="'small'" circle @click="createNewSession">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </el-button>
      </el-tooltip>
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
        />
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
import { ref, nextTick, inject } from 'vue'
import { ElABubble, ElABubbleList, ElASender, ElAThinking, ElAMarkdown } from 'element-ai-vue'

const SERVER_URL = 'http://127.0.0.1:4096'
const bubbleListRef = ref(null)
const mapContainer = inject('mapContainer')

const messages = ref([])
const inputText = ref('')
const currentSessionId = ref(null)
const modelOptions = ref([])
const selectedModel = ref('')

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

function scrollToBottom() {
  nextTick(() => {
    if (bubbleListRef.value?.scrollToBottom) {
      bubbleListRef.value.scrollToBottom()
    }
  })
}

async function handleSend(text) {
  if (!currentSessionId.value) {
    const created = await createSession()
    if (!created) return
  }

  addMessage('user', text)
  inputText.value = ''

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
        parts: [{ type: 'text', text }]
      })
    })

    messages.value = messages.value.filter(m => m.id !== loadingMsg.id)

    if (response.ok) {
      const result = await response.json()
      renderResponseParts(result.parts)
    } else {
      const errorText = await response.text()
      addMessage('assistant', `请求失败: ${errorText}`)
    }
  } catch (error) {
    messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
    addMessage('assistant', `请求失败: ${error.message}`)
  }
}

function renderResponseParts(parts) {
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
  const connected = await checkServerHealth()
  if (connected) {
    await fetchModels()
    await createSession()
    // testMapFunctions()
  }
}

init()
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
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.chat-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

:deep(.el-ai-bubble) {
  margin-bottom: 12px;
}

:deep(.el-ai-bubble:last-child) {
  margin-bottom: 0;
}

:deep(.el-ai-thinking) {
  margin-bottom: 12px;
}

.chat-input-area {
  padding: 8px 16px 16px;
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
</style>