// web/src/composables/opencode/useOpenCodeAPI.js

import { AGENT_COLORS } from '../../components/opencode/utils.js'

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

export function useOpenCodeAPI({
  serverUrl,
  messages,
  sessionBusy,
  selectedAgent,
  selectedModel,
  modelOptions,
  agents,
  currentSessionId,
  pendingQuestion,
  pendingPermission,
  todos,
  addSystemMessage,
  addToolCallMsg,
  clearSubSessionTracking,
  setCommandSourceMap,
  subAgentNames,
  subSessionIds,
  onNewSession,
  defaultAgent,
  defaultModel,
}) {
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
      if (defaultAgent && mapped.some(a => a.value === defaultAgent)) {
        selectedAgent.value = defaultAgent
      }
    } catch (e) {
      console.error('[fetchAgents]', e)
    }
  }

  async function fetchModels() {
    try {
      const r = await fetch(`${serverUrl}/config/providers`)
      if (!r.ok) return
      const data = await r.json()
      const list = []
      for (const provider of data.providers || []) {
        for (const model of Object.values(provider.models || {})) {
          const variants = model.variants ? Object.keys(model.variants) : undefined
          list.push({
            value: model.id,
            providerID: model.providerID,
            name: model.name || model.id,
            label: `${provider.name} - ${model.name || model.id}`,
            group: provider.name,
            variants,
          })
        }
      }
      if (!list.length) return
      modelOptions.value = list
      if (defaultModel && list.some(o => o.value === defaultModel)) {
        selectedModel.value = defaultModel
      } else {
        selectedModel.value = list.find(o => o.value === 'minimax-m2.5-free')?.value || list[0].value
      }
    } catch (e) {
      console.error('[fetchModels]', e)
    }
  }

  async function fetchCommands() {
    try {
      const r = await fetch(`${serverUrl}/command`)
      if (!r.ok) return
      const list = await r.json()
      const entries = []
      for (const cmd of list) {
        if (cmd.source) {
          entries.push([cmd.name.toLowerCase(), cmd.source])
        }
      }
      setCommandSourceMap(entries)
    } catch (e) {
      console.error('[fetchCommands]', e)
    }
  }

  async function createSession() {
    try {
      const r = await fetch(`${serverUrl}/session`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      if (r.ok) { currentSessionId.value = (await r.json()).id; return true }
    } catch (e) {
      console.error('[createSession]', e)
    }
    return false
  }

  async function handleSend({ text, agent, model, thinkingEffort, points }) {
    if (!currentSessionId.value) {
      if (!(await createSession())) return
    }

    const pointsArr = points || []
    let fullText = text
    if (pointsArr.length > 0) {
      fullText = `[地图标注点]\n${pointsArr.map(p => `${p.label} (${p.lng}, ${p.lat})`).join('\n')}\n\n[用户问题]\n${text}`
    }
    messages.value.push({ id: uid(), type: 'message', role: 'user', content: fullText, points: pointsArr.length > 0 ? pointsArr : undefined, userText: text })
    sessionBusy.value = true
    clearSubSessionTracking()

    const loadingMsg = { id: uid(), type: 'message', role: 'assistant', content: '', loading: true, typing: false }
    messages.value.push(loadingMsg)

    try {
      const m = modelOptions.value.find(o => o.value === model)
      const response = await fetch(`${serverUrl}/session/${currentSessionId.value}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent: agent || 'gis-orchestrator',
          model: m ? { providerID: m.providerID, modelID: m.value } : undefined,
          parts: [{ type: 'text', text: fullText }],
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
          // Text will arrive via SSE — keep loading message
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
      const r = await fetch(`${serverUrl}/question/${requestID}/reject`, { method: 'POST' })
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
    clearSubSessionTracking()
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
    const realMsgs = messages.value.filter(m => m.type !== 'system')
    if (currentSessionId.value && realMsgs.length === 0 && !sessionBusy.value) {
      addSystemMessage('当前已是新会话')
      return
    }
    if (onNewSession) onNewSession()
    messages.value = []
    sessionBusy.value = false
    clearSubSessionTracking()
    await createSession()
    addSystemMessage('已创建新会话')
  }

  async function fetchSessionList() {
    try {
      const r = await fetch(`${serverUrl}/session`)
      if (!r.ok) return []
      const data = await r.json()
      return data || []
    } catch (e) {
      console.error('[fetchSessionList]', e)
      return []
    }
  }

  async function switchSession(sessionId) {
    try {
      const r = await fetch(`${serverUrl}/session/${sessionId}/message`)
      if (!r.ok) return false
      const data = await r.json()
      messages.value = []
      sessionBusy.value = false
      clearSubSessionTracking()
      currentSessionId.value = sessionId

      for (const msg of data) {
        const isUser = msg.info?.role === 'user'
        const isAssistant = msg.info?.role === 'assistant'
        if (!isUser && !isAssistant) continue
        const parts = msg.parts || []
        for (const part of parts) {
          if (part.type === 'text' && part.text) {
            messages.value.push({
              id: uid(),
              type: 'message',
              role: isUser ? 'user' : 'assistant',
              content: part.text,
              loading: false,
              typing: false,
            })
          } else if (part.type === 'reasoning' && part.text) {
            messages.value.push({
              id: uid(),
              type: 'reasoning',
              content: part.text,
              expanded: false,
            })
          } else if (part.type === 'tool') {
            const toolName = part.tool || 'unknown'
            const state = part.state || {}
            const status = state.status || 'completed'
            const input = state.input
            const output = state.output
            const metadata = state.metadata || {}
            const subSessionId = metadata.sessionId
            const agentName = metadata?.agent || metadata?.name || (toolName === 'task' && input?.subagent_type)
            addToolCallMsg(part.id, toolName, status, input, output, subSessionId, agentName)
          }
        }
      }
      addSystemMessage(`已切换到会话 ${sessionId.slice(0, 8)}`)
      return true
    } catch (e) {
      console.error('[switchSession]', e)
      return false
    }
  }

  async function deleteSession(sessionId) {
    try {
      const r = await fetch(`${serverUrl}/session/${sessionId}`, { method: 'DELETE' })
      return r.ok
    } catch (e) {
      console.error('[deleteSession]', e)
      return false
    }
  }

  async function fetchTodos() {
    if (!currentSessionId.value) return
    try {
      const r = await fetch(`${serverUrl}/session/${currentSessionId.value}/todo`)
      if (!r.ok) return
      const data = await r.json()
      todos.value = Array.isArray(data) ? data : (data?.items || data?.todos || [])
    } catch (e) {
      console.error('[fetchTodos]', e)
    }
  }

  return {
    fetchAgents,
    fetchModels,
    fetchCommands,
    createSession,
    handleSend,
    handleAbort,
    handleNewSession,
    answerQuestion,
    cancelQuestion,
    respondPermission,
    fetchSessionList,
    switchSession,
    deleteSession,
    fetchTodos,
  }
}
