import { ref } from 'vue'

const AGENT_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f97316', '#ef4444']

export function useOpenCodeChat(serverUrl = 'http://127.0.0.1:4096') {
  const messages = ref([])
  const sessionBusy = ref(false)
  const selectedAgent = ref('')
  const selectedModel = ref('')
  const modelOptions = ref([])
  const agents = ref([])
  const currentSessionId = ref(null)
  const serverConnected = ref(false)
  const pendingQuestion = ref(null)
  const pendingPermission = ref(null)

  let eventSource = null
  let eventReconnectTimer = null
  const commandSourceMap = {}
  const subSessionIds = new Set()
  const subAgentNames = {}
  const partTypeByID = {}
  const streamingPartIds = new Set()
  let currentUserMessageId = null
  let flushTimer = null
  let eventQueue = []
  const staleDeltas = new Set()
  const coalescedKeys = new Map()

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function countLabel(toolCount, skillCount) {
  const parts = []
  if (toolCount) parts.push(`${toolCount} tool${toolCount > 1 ? 's' : ''}`)
  if (skillCount) parts.push(`${skillCount} skill${skillCount > 1 ? 's' : ''}`)
  return parts.join(' + ') || '0 tools'
}

  function addSystemMessage(text) {
    messages.value.push({ id: uid(), type: 'system', content: text })
  }

  function setMessages(val) { messages.value = val }

  // --- Event coalescing queue ---

  function coalesceKey(payload) {
    const p = payload.properties || {}
    if (payload.type === 'session.status') return `ss:${p.sessionID}`
    if (payload.type === 'message.part.updated') {
      const part = p.part
      if (!part) return
      return `mpu:${part.messageID}:${part.id}`
    }
  }

  function pushEvent(payload) {
    const k = coalesceKey(payload)
    if (k) {
      const i = coalescedKeys.get(k)
      if (i !== undefined) {
        eventQueue[i] = payload
        if (payload.type === 'message.part.updated') {
          const part = payload.properties?.part
          if (part) staleDeltas.add(`${part.messageID}:${part.id}`)
        }
        scheduleFlush()
        return
      }
      coalescedKeys.set(k, eventQueue.length)
    } else if (payload.type === 'message.part.delta') {
      const p = payload.properties || {}
      if (staleDeltas.has(`${p.messageID}:${p.partID}`)) return
    }
    eventQueue.push(payload)
    scheduleFlush()
  }

  function scheduleFlush() {
    if (flushTimer) return
    flushTimer = setTimeout(flushEvents, 16)
  }

  function flushEvents() {
    flushTimer = null
    if (eventQueue.length === 0) return
    const batch = eventQueue
    eventQueue = []
    coalescedKeys.clear()
    staleDeltas.clear()
    for (const payload of batch) {
      processEvent(payload)
    }
  }

  function flushImmediate() {
    if (flushTimer) {
      clearTimeout(flushTimer)
      flushTimer = null
    }
    flushEvents()
  }

  // --- SSE ---

  function connectEventSource() {
    if (eventSource) return
    eventSource = new EventSource(`${serverUrl}/global/event`)
    eventSource.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data)
        const payload = parsed?.payload
        if (!payload) return
        pushEvent(payload)
      } catch {}
    }
    eventSource.onerror = () => {
      flushImmediate()
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

  function processEvent(payload) {
    const props = payload.properties || {}
    if (!currentSessionId.value) return
    if (props.sessionID !== currentSessionId.value && !subSessionIds.has(props.sessionID)) return

    switch (payload.type) {
      case 'session.status': {
        const s = props.status?.type
        if (s === 'busy') sessionBusy.value = true
        else if (s === 'idle') {
          sessionBusy.value = false
          streamingPartIds.clear()
          for (const m of messages.value) {
            if (m._sse) m._finalized = true
            if (m.typing) m.typing = false
          }
          const loading = messages.value.find(m => m.loading && m.role === 'assistant')
          if (loading) messages.value = messages.value.filter(m => m.id !== loading.id)
        }
        break
      }
      case 'message.updated': {
        if (props.info?.role === 'user') currentUserMessageId = props.info.id
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
      case 'question.asked': {
        const qid = props.id || props.requestID
        pendingQuestion.value = { ...props, id: qid, requestID: qid }
        break
      }
      case 'question.replied':
      case 'question.rejected': {
        if (pendingQuestion.value && (props.requestID === pendingQuestion.value.id || props.requestID === pendingQuestion.value.requestID)) {
          pendingQuestion.value = null
        }
        break
      }
      case 'permission.asked': {
        pendingPermission.value = { ...props, id: props.id || props.requestID, requestID: props.id || props.requestID }
        break
      }
      case 'permission.replied': {
        if (pendingPermission.value && (props.requestID === pendingPermission.value.id || props.requestID === pendingPermission.value.requestID)) {
          pendingPermission.value = null
        }
        break
      }
    }
  }

  function handleStreamDelta(props) {
    const { partID, delta, messageID, sessionID } = props
    if (messageID && currentUserMessageId && messageID === currentUserMessageId) return

    if (sessionID && subSessionIds.has(sessionID)) {
      const parent = messages.value.find(m => m.type === 'tool_call' && m.subSessionId === sessionID)
      if (!parent) return
      if (partTypeByID[partID] === 'reasoning') {
        parent._subReasoning = (parent._subReasoning || '') + delta
        if (parent.subStatus !== 'completed') parent._subStatusText = '思考中...'
      } else {
        parent._subText = (parent._subText || '') + delta
        if (parent.subStatus !== 'completed') parent._subStatusText = '回复中...'
      }
      return
    }

    if (!streamingPartIds.has(partID)) {
      streamingPartIds.add(partID)
      if (streamingPartIds.size === 1) {
        const last = messages.value[messages.value.length - 1]
        if (last && last.type === 'message' && last.role === 'assistant' && last.loading) {
          messages.value = messages.value.filter(m => m.id !== last.id)
        }
      }
    }

    const reasoningMsg = messages.value.find(m => m._partId === partID && m._sse && m.type === 'reasoning')
    if (reasoningMsg) { reasoningMsg.content += delta; return }
    const textMsg = messages.value.find(m => m._partId === partID && m._sse && m.type === 'message' && m.role === 'assistant')
    if (textMsg) { textMsg.content += delta; textMsg.typing = true; textMsg.loading = false; return }
  }

  function handlePartUpdated(part) {
    if (!part || !part.type) return
    if (part.messageID && currentUserMessageId && part.messageID === currentUserMessageId) return
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
            parent._subStatusText = `已完成 (${countLabel(parent._toolCount || 0, parent._skillCount || 0)})`
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
            if (parent.subStatus !== 'completed') parent._subStatusText = `调用工具: ${toolName}`
            if (!parent._subTools) parent._subTools = []
            const existing = parent._subTools.find(t => t.partID === part.id)
            if (existing) {
              existing.status = status
              if (input !== undefined) existing.input = input
              if (output !== undefined) existing.output = output
            } else {
              const source = commandSourceMap[toolName.toLowerCase()] || 'command'
              if (source === 'skill') parent._skillCount = (parent._skillCount || 0) + 1
              else parent._toolCount = (parent._toolCount || 0) + 1
              parent._subTools.push({ id: uid(), partID: part.id, tool: toolName, status, input, output, _expanded: false })
            }
            if (status === 'completed' || status === 'failed') {
              const allTools = parent._subTools || []
              const allDone = allTools.every(t => t.status === 'completed' || t.status === 'failed')
              if (allDone) {
                const countInfo = countLabel(parent._toolCount || 0, parent._skillCount || 0)
                // Only mark completed if text has already arrived (streaming done)
                // Otherwise, wait for text part update to set completed
                if (parent._subText) {
                  parent.subStatus = 'completed'
                  parent._subStatusText = `已完成 (${countInfo})`
                } else {
                  parent._subStatusText = `等待回复... (${countInfo})`
                }
              }
            }
          }
        } else {
          const resolvedAgentName = agentName || (subSessionId ? subAgentNames[subSessionId] : undefined)
          addToolCallMsg(part.id, toolName, status, input, output, subSessionId, resolvedAgentName)
          if (subSessionId) {
            subSessionIds.add(subSessionId)
            if (agentName) subAgentNames[subSessionId] = agentName
          }
        }
        break
      }
    }
  }

  function addToolCallMsg(partID, toolName, status, input, output, subSessionId, agentName) {
    if (status === 'pending') return
    const existing = messages.value.find(m =>
      m.type === 'tool_call' && m.partID === partID
    )
    if (existing) {
      existing.status = status
      if (output !== undefined) existing.output = output
      if (subSessionId && !existing.subSessionId) existing.subSessionId = subSessionId
      if (agentName && !existing.agent) existing.agent = agentName
      return
    }
    messages.value.push({
      id: uid(), partID, type: 'tool_call', toolName, status, input, output,
      subSessionId, subStatus: subSessionId ? 'running' : undefined,
      agent: agentName, _expanded: false,
    })
  }

  // --- API ---

  async function fetchAgents() {
    try {
      const r = await fetch(`${serverUrl}/agent`)
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

  async function fetchModels() {
    try {
      const r = await fetch(`${serverUrl}/config/providers`)
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

  async function fetchCommands() {
    try {
      const r = await fetch(`${serverUrl}/command`)
      if (!r.ok) return
      const list = await r.json()
      for (const cmd of list) {
        if (cmd.source) commandSourceMap[cmd.name.toLowerCase()] = cmd.source
      }
    } catch {}
  }

  async function createSession() {
    try {
      const r = await fetch(`${serverUrl}/session`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      if (r.ok) { currentSessionId.value = (await r.json()).id; return true }
    } catch {}
    return false
  }

  async function handleSend({ text, agent, model, thinkingEffort }) {
    if (!currentSessionId.value) {
      if (!(await createSession())) return
    }

    messages.value.push({ id: uid(), type: 'message', role: 'user', content: text })
    sessionBusy.value = true
    streamingPartIds.clear()
    currentUserMessageId = null
    subSessionIds.clear()

    const loadingMsg = { id: uid(), type: 'message', role: 'assistant', content: '', loading: true, typing: false }
    messages.value.push(loadingMsg)

    try {
      const m = modelOptions.value.find(o => o.value === model)
      const response = await fetch(`${serverUrl}/session/${currentSessionId.value}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent: agent || 'orchestrator',
          model: m ? { providerID: m.providerID, modelID: m.value } : undefined,
          parts: [{ type: 'text', text }],
          settings: m?.variants?.length && thinkingEffort ? { thinkingEffort } : undefined,
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
            const existing = messages.value.find(mm => mm._partId === part.id && mm.type === 'message' && mm.role === 'assistant')
            if (!existing) messages.value.push({ id: uid(), _partId: part.id, _sse: true, type: 'message', role: 'assistant', content: part.text, loading: false, typing: false })
          } else if (part.type === 'tool') {
            const toolName = part.tool || 'unknown'
            const status = part.state?.status || 'completed'
            const input = part.state?.input
            const output = part.state?.output
            const metadata = part.state?.metadata
            const subSessionId = metadata?.sessionId
            const agentName = metadata?.agent || metadata?.name || (toolName === 'task' && input?.subagent_type)
            const resolvedAgentName = agentName || (subSessionId ? subAgentNames[subSessionId] : undefined)
            addToolCallMsg(part.id, toolName, status, input, output, subSessionId, resolvedAgentName)
            if (subSessionId) { subSessionIds.add(subSessionId); if (resolvedAgentName) subAgentNames[subSessionId] = resolvedAgentName }
          }
        }
        if (!hasTextContent) {
          // Text will arrive via SSE — keep loading message, let session.status:idle handle cleanup
        } else {
          for (const mm of messages.value) { if (mm.typing) mm.typing = false }
        }
      } else {
        messages.value = messages.value.filter(mm => mm.id !== loadingMsg.id)
        messages.value.push({ id: uid(), type: 'message', role: 'assistant', content: `请求失败: ${await response.text()}` })
        sessionBusy.value = false
      }
    } catch (error) {
      messages.value = messages.value.filter(mm => mm.id !== loadingMsg.id)
      messages.value.push({ id: uid(), type: 'message', role: 'assistant', content: `请求失败: ${error.message}` })
      sessionBusy.value = false
    }
  }

  async function answerQuestion(answers) {
    const q = pendingQuestion.value
    if (!q) return
    const requestID = q.id || q.requestID
    pendingQuestion.value = null
    try {
      const r = await fetch(`${serverUrl}/question/${requestID}/reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers }),
      })
      if (!r.ok) console.error('[question] reply failed', r.status, await r.text().catch(() => ''))
    } catch (e) {
      console.error('[question] reply error', e)
    }
  }

  async function cancelQuestion() {
    const q = pendingQuestion.value
    if (!q) return
    const requestID = q.id || q.requestID
    pendingQuestion.value = null
    try {
      const r = await fetch(`${serverUrl}/question/${requestID}/reject`, {
        method: 'POST',
      })
      if (!r.ok) console.error('[question] reject failed', r.status, await r.text().catch(() => ''))
    } catch (e) {
      console.error('[question] reject error', e)
    }
  }

  async function respondPermission(response) {
    const p = pendingPermission.value
    if (!p) return
    const requestID = p.id || p.requestID
    pendingPermission.value = null
    try {
      const r = await fetch(`${serverUrl}/permission/${requestID}/reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reply: response }),
      })
      if (!r.ok) console.error('[permission] reply failed', r.status, await r.text().catch(() => ''))
    } catch (e) {
      console.error('[permission] reply error', e)
    }
  }

  async function handleAbort() {
    if (!currentSessionId.value) return
    try { await fetch(`${serverUrl}/session/${currentSessionId.value}/abort`, { method: 'POST' }) } catch {}
    sessionBusy.value = false
    streamingPartIds.clear()
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
    streamingPartIds.clear()
    subSessionIds.clear()
    await createSession()
    addSystemMessage('已创建新会话')
  }

  async function init() {
    connectEventSource()
    try {
      const r = await fetch(`${serverUrl}/global/health`)
      if (r.ok) {
        serverConnected.value = true
        addSystemMessage(`已连接至 OpenCode 服务器，版本: ${(await r.json()).version}`)
        await fetchAgents()
        await fetchCommands()
        await fetchModels()
        await createSession()
      } else {
        addSystemMessage('无法连接 OpenCode 服务器，请确保已运行 opencode serve')
      }
    } catch {
    addSystemMessage('无法连接 OpenCode 服务器，请确保已运行 opencode serve')
    }
  }

  function cleanup() {
    disconnectEventSource()
  }

  return {
    messages,
    setMessages,
    sessionBusy,
    selectedAgent,
    selectedModel,
    modelOptions,
    agents,
    serverConnected,
    pendingQuestion,
    pendingPermission,
    handleSend,
    handleAbort,
    handleNewSession,
    answerQuestion,
    cancelQuestion,
    respondPermission,
    init,
    cleanup,
  }
}
