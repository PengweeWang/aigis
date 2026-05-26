// web/src/composables/opencode/useMessageHandler.js

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function countLabel(toolCount, skillCount) {
  const parts = []
  if (toolCount) parts.push(`${toolCount} tool${toolCount > 1 ? 's' : ''}`)
  if (skillCount) parts.push(`${skillCount} skill${skillCount > 1 ? 's' : ''}`)
  return parts.join(' + ') || '0 tools'
}

export function useMessageHandler({ messages, sessionBusy, currentSessionId }) {
  const commandSourceMap = {}
  const subSessionIds = new Set()
  const subAgentNames = {}
  const partTypeByID = {}
  const streamingPartIds = new Set()
  let currentUserMessageId = null

  function addSystemMessage(text) {
    messages.value.push({ id: uid(), type: 'system', content: text })
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
        return { type: 'question', data: { ...props, id: qid, requestID: qid } }
      }
      case 'question.replied':
      case 'question.rejected': {
        return { type: 'question-clear', data: props }
      }
      case 'permission.asked': {
        return { type: 'permission', data: { ...props, id: props.id || props.requestID, requestID: props.id || props.requestID } }
      }
      case 'permission.replied': {
        return { type: 'permission-clear', data: props }
      }
      case 'todo.updated': {
        return { type: 'todo', data: props }
      }
    }
    return null
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

  function clearSubSessionTracking() {
    streamingPartIds.clear()
    subSessionIds.clear()
    currentUserMessageId = null
  }

  function setCommandSourceMap(entries) {
    for (const [name, source] of entries) {
      commandSourceMap[name] = source
    }
  }

  return {
    processEvent,
    addSystemMessage,
    addToolCallMsg,
    clearSubSessionTracking,
    setCommandSourceMap,
    subAgentNames,
    subSessionIds,
  }
}
