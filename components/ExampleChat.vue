<template>
  <OpenCodeChatPanel
    v-model:messages="messages"
    :agents="agents"
    v-model:selectedAgent="selectedAgent"
    :sessionBusy="sessionBusy"
    :modelOptions="modelOptions"
    v-model:selectedModel="selectedModel"
    v-model:thinkingEffort="thinkingEffort"
    v-model:panelWidth="panelWidth"
    :minPanelWidth="350"
    title="OpenCode Chat"
    @send="handleSend"
    @abort="handleAbort"
    @new-session="handleNewSession"
  />
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import OpenCodeChatPanel from './OpenCodeChatPanel.vue'

const SERVER_URL = 'http://127.0.0.1:4096'

const messages = ref([])
const sessionBusy = ref(false)
const selectedAgent = ref('')
const selectedModel = ref('')
const modelOptions = ref([])
const panelWidth = ref(Math.round(window.innerWidth * 0.3))
const thinkingEffort = ref('medium')
const currentSessionId = ref(null)
const streamingPartId = ref(null)
const currentUserMessageId = ref(null)
const subSessionIds = new Set()
const subAgentNames = {}
const deltaAccum = {}
const partTypeByID = {}

const agents = ref([])
const AGENT_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f97316', '#ef4444']

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function addSystemMessage(text) {
  messages.value.push({ id: uid(), type: 'system', content: text })
}

function addMessage(role, content, extra = {}) {
  messages.value.push({ id: uid(), type: 'message', role, content, ...extra })
}

function addToolCallMsg(toolName, status, input, output, subSessionId, agentName) {
  if (status === 'pending') return null
  const existing = messages.value.find(m =>
    m.type === 'tool_call' && m.toolName === toolName && (m.status === 'running' || m.status === 'pending')
  )
  if (existing) {
    existing.status = status
    if (output !== undefined) existing.output = output
    if (subSessionId && !existing.subSessionId) existing.subSessionId = subSessionId
    return existing
  }
  const msg = {
    id: uid(), type: 'tool_call', toolName, status, input, output,
    subSessionId, subStatus: subSessionId ? 'running' : undefined,
    agent: agentName, _expanded: false,
  }
  messages.value.push(msg)
  return msg
}

// --- SSE ---
let eventSource = null
let eventReconnectTimer = null

function connectEventSource() {
  if (eventSource) return
  eventSource = new EventSource(`${SERVER_URL}/global/event`)
  eventSource.onmessage = (e) => {
    try { handleGlobalEvent(JSON.parse(e.data)) } catch {}
  }
  eventSource.onerror = () => {
    disconnectEventSource()
    eventReconnectTimer = setTimeout(connectEventSource, 3000)
  }
}

function disconnectEventSource() {
  clearTimeout(eventReconnectTimer)
  if (eventSource) {
    eventSource.onmessage = null; eventSource.onerror = null
    eventSource.close(); eventSource = null
  }
}

function handleGlobalEvent(event) {
  const payload = event?.payload
  if (!payload) return
  const props = payload.properties || {}
  if (!currentSessionId.value) return
  if (props.sessionID !== currentSessionId.value && !subSessionIds.has(props.sessionID)) return

  switch (payload.type) {
    case 'session.status': {
      const s = props.status?.type
      if (s === 'busy') sessionBusy.value = true
      else if (s === 'idle') {
        sessionBusy.value = false
        streamingPartId.value = null
        const loading = messages.value.find(m => m.loading && m.role === 'assistant')
        if (loading) messages.value = messages.value.filter(m => m.id !== loading.id)
      }
      break
    }
    case 'message.updated': {
      if (props.info?.role === 'user') currentUserMessageId.value = props.info.id
      break
    }
    case 'message.part.delta': {
      if (props.field === 'text' && props.delta) handleStreamDelta(props)
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
  if (messageID && currentUserMessageId.value && messageID === currentUserMessageId.value) return
  if (messages.value.find(m => m._finalized && m.type === 'message' && m.role === 'assistant')) return

  if (sessionID && subSessionIds.has(sessionID)) {
    const parent = messages.value.find(m => m.type === 'tool_call' && m.subSessionId === sessionID)
    if (!parent) return
    deltaAccum[partID] = (deltaAccum[partID] || '') + delta
    if (partTypeByID[partID] === 'reasoning') {
      parent._subReasoning = deltaAccum[partID]
      if (parent.subStatus !== 'completed') parent._subStatusText = '思考中...'
    } else {
      parent._subText = deltaAccum[partID]
      if (parent.subStatus !== 'completed') parent._subStatusText = '回复中...'
    }
    return
  }

  deltaAccum[partID] = (deltaAccum[partID] || '') + delta
  if (!streamingPartId.value || streamingPartId.value !== partID) {
    streamingPartId.value = partID
    const last = messages.value[messages.value.length - 1]
    if (last && last.type === 'message' && last.role === 'assistant' && last.loading) {
      messages.value = messages.value.filter(m => m.id !== last.id)
    }
  }

  const fullText = deltaAccum[partID]
  const reasoningMsg = messages.value.find(m => m._partId === partID && m._sse && m.type === 'reasoning')
  if (reasoningMsg) { reasoningMsg.content = fullText; return }
  const textMsg = messages.value.find(m => m._partId === partID && m._sse && m.type === 'message' && m.role === 'assistant')
  if (textMsg) { textMsg.content = fullText; textMsg.typing = true; textMsg.loading = false; return }
}

function handlePartUpdated(part) {
  if (!part || !part.type) return
  if (part.messageID && currentUserMessageId.value && part.messageID === currentUserMessageId.value) return
  delete deltaAccum[part.id]
  if (['step-start', 'step-finish', 'snapshot', 'patch'].includes(part.type)) return
  partTypeByID[part.id] = part.type
  const text = part.text || ''
  const isSubSession = part.sessionID && subSessionIds.has(part.sessionID)

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
          parent._subStatusText = '已完成'
        }
      }
    }
    return
  }

  switch (part.type) {
    case 'text': {
      const existing = messages.value.find(m => m._partId === part.id && m._sse && m.type === 'message' && m.role === 'assistant')
      if (existing) { existing.content = text; existing.typing = false }
      else messages.value.push({ id: uid(), _partId: part.id, _sse: true, type: 'message', role: 'assistant', content: text, loading: !text, typing: false })
      break
    }
    case 'reasoning': {
      const existing = messages.value.find(m => m._partId === part.id && m._sse && m.type === 'reasoning')
      if (existing) existing.content = text
      else messages.value.push({ id: uid(), _partId: part.id, _sse: true, type: 'reasoning', content: text, expanded: false })
      break
    }
    case 'tool': {
      const toolName = part.tool || 'unknown'
      const state = part.state || {}
      const status = state.status || 'running'
      const input = state.input; const output = state.output
      const metadata = state.metadata || {}
      const subSessionId = metadata.sessionId
      const agentName = metadata?.agent || metadata?.name || (toolName === 'task' && input?.subagent_type)

      if (part.sessionID && subSessionIds.has(part.sessionID)) {
        if (status === 'pending') break
        const parent = messages.value.find(m => m.type === 'tool_call' && m.subSessionId === part.sessionID)
        if (parent) {
          if (!parent._subTools) parent._subTools = []
          const existing = parent._subTools.find(t => t.tool === toolName && t.status === 'running')
          if (existing) { existing.status = status; if (input !== undefined) existing.input = input; if (output !== undefined) existing.output = output }
          else parent._subTools.push({ id: uid(), tool: toolName, status, input, output, _expanded: false })
          if (status === 'completed' || status === 'failed') {
            const allDone = parent._subTools?.every(t => t.status === 'completed' || t.status === 'failed')
            if (allDone) {
              // Only mark completed if text has already arrived (streaming done)
              if (parent._subText) {
                parent.subStatus = 'completed'
                parent._subStatusText = '已完成'
              } else {
                parent.subStatus = 'running'
                parent._subStatusText = '等待回复...'
              }
            }
          }
        }
      } else {
        addToolCallMsg(toolName, status, input, output, subSessionId, agentName)
        if (subSessionId) {
          subSessionIds.add(subSessionId)
          if (agentName) subAgentNames[subSessionId] = agentName
        }
      }
      break
    }
  }
}

// --- API ---

async function fetchAgents() {
  try {
    const r = await fetch(`${SERVER_URL}/agent`)
    if (!r.ok) return
    const list = await r.json()
    const mapped = list
      .filter(a => !a.hidden && a.mode === 'primary')
      .map((a, i) => ({
        value: a.name,
        label: a.name,
        color: a.color || AGENT_COLORS[i % AGENT_COLORS.length],
      }))
    agents.value = mapped
    if (mapped.length > 0 && !selectedAgent.value) {
      selectedAgent.value = mapped[0].value
    }
  } catch {}
}

async function createSession() {
  try {
    const r = await fetch(`${SERVER_URL}/session`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
    if (r.ok) {
      currentSessionId.value = (await r.json()).id
      return true
    }
  } catch {}
  return false
}

async function fetchModels() {
  try {
    const r = await fetch(`${SERVER_URL}/config/providers`)
    if (!r.ok) return
    const data = await r.json()
    const options = []
    for (const provider of data.providers || []) {
      for (const model of Object.values(provider.models || {})) {
        const variants = model.variants ? Object.keys(model.variants) : undefined
        options.push({
          value: model.id,
          providerID: model.providerID,
          name: model.name || model.id,
          label: `${provider.name} - ${model.name || model.id}`,
          group: provider.name,
          variants,
        })
      }
    }
    if (!options.length) return
    modelOptions.value = options
    selectedModel.value = options.find(o => o.value === 'minimax-m2.5-free')?.value || options[0].value
  } catch {}
}

// --- Event handlers ---

async function handleSend({ text, agent, model }) {
  if (!currentSessionId.value) {
    if (!(await createSession())) return
  }

  addMessage('user', text)
  sessionBusy.value = true
  streamingPartId.value = null
  currentUserMessageId.value = null
  subSessionIds.clear()

  const loadingMsg = { id: uid(), type: 'message', role: 'assistant', content: '', loading: true, typing: false }
  messages.value.push(loadingMsg)

  try {
    const m = modelOptions.value.find(o => o.value === model)
    const response = await fetch(`${SERVER_URL}/session/${currentSessionId.value}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent: agent || 'orchestrator',
        model: m ? { providerID: m.providerID, modelID: m.value } : undefined,
        parts: [{ type: 'text', text }],
        settings: m?.variants?.length && thinkingEffort.value ? { thinkingEffort: thinkingEffort.value } : undefined,
      }),
    })

    if (response.ok) {
      const result = await response.json()
      const rawParts = Array.isArray(result) ? result : (result.parts || [])
      let hasTextContent = false
      for (const part of rawParts) {
        if (part.type === 'text' && part.text) {
          hasTextContent = true
          messages.value = messages.value.filter(mm => mm.id !== loadingMsg.id)
          messages.value.push({ id: uid(), _partId: part.id, _sse: true, type: 'message', role: 'assistant', content: part.text, loading: false, typing: false })
        } else if (part.type === 'tool') {
          const toolName = part.tool || 'unknown'
          const status = part.state?.status || 'completed'
          const input = part.state?.input
          const output = part.state?.output
          const metadata = part.state?.metadata
          const subSessionId = metadata?.sessionId
          const agentName = metadata?.agent || metadata?.name || (toolName === 'task' && input?.subagent_type)
          addToolCallMsg(toolName, status, input, output, subSessionId, agentName)
          if (subSessionId) {
            subSessionIds.add(subSessionId)
            if (agentName) subAgentNames[subSessionId] = agentName
          }
        }
      }
      if (!hasTextContent) {
        // Text will arrive via SSE — keep loading message, let session.status:idle handle cleanup
      } else {
        for (const mm of messages.value) { if (mm.typing) mm.typing = false }
      }
    } else {
      messages.value = messages.value.filter(mm => mm.id !== loadingMsg.id)
      addMessage('assistant', `请求失败: ${await response.text()}`)
      sessionBusy.value = false
    }
  } catch (error) {
    messages.value = messages.value.filter(mm => mm.id !== loadingMsg.id)
    addMessage('assistant', `请求失败: ${error.message}`)
    sessionBusy.value = false
  }
}

async function handleAbort() {
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

async function handleNewSession() {
  messages.value = []
  sessionBusy.value = false
  streamingPartId.value = null
  subSessionIds.clear()
  await createSession()
  addSystemMessage('已创建新会话')
}

// --- Init ---

onMounted(async () => {
  connectEventSource()
  try {
    const r = await fetch(`${SERVER_URL}/global/health`)
    if (r.ok) {
      addSystemMessage(`已连接至 OpenCode 服务器，版本: ${(await r.json()).version}`)
      await fetchAgents()
      await fetchModels()
      await createSession()
    } else {
      addSystemMessage('无法连接 OpenCode 服务器，请确保已运行 opencode serve')
    }
  } catch {
    addSystemMessage('无法连接 OpenCode 服务器，请确保已运行 opencode serve')
  }
})

onUnmounted(() => {
  disconnectEventSource()
})
</script>
