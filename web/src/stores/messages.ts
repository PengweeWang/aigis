import { defineStore } from 'pinia'
import { ref, nextTick } from 'vue'
import { useSessionStore } from './session'
import { useStreamingStore } from './streaming'

// Use relative paths — Vite proxy handles routing to opencode (4096)

export const useMessagesStore = defineStore('messages', () => {
  /** @type {import('vue').Ref<import('../lib/contracts').Message[]>} */
  const items = ref([])
  const loadingMessageId = ref(null)
  /** @type {(() => void) | null} */
  let scrollCallback = null

  function registerScroll(fn) {
    scrollCallback = fn
  }

  function scrollToBottom() {
    nextTick(() => {
      scrollCallback?.()
    })
  }

  function addSystemMessage(content) {
    items.value.push({
      id: Date.now().toString() + '-system',
      type: 'system',
      content,
    })
    scrollToBottom()
  }

  /** @param {import('../lib/contracts').UserPoint[]} [points] */
  function addUserMessage(formattedText, points, originalText) {
    items.value.push({
      id: Date.now().toString() + '-user',
      type: 'message',
      role: 'user',
      content: formattedText,
      points: points?.length ? points : undefined,
      userText: originalText || formattedText,
    })
    scrollToBottom()
  }

  function setLoadingPlaceholder() {
    const id = Date.now().toString() + '-loading'
    loadingMessageId.value = id
    items.value.push({
      id,
      type: 'message',
      role: 'assistant',
      content: '',
      loading: true,
      typing: false,
    })
    scrollToBottom()
  }

  /** @param {import('../lib/contracts').SsePayload} msg */
  function applySSEEvent(msg) {
    const sessionStore = useSessionStore()
    const streamingStore = useStreamingStore()
    const payload = msg.payload
    if (!payload?.properties) return

    const props = payload.properties
    if (props.sessionID !== sessionStore.sessionId) return

    switch (payload.type) {
      case 'message.updated': {
        if (props.info?.role === 'assistant') {
          // Remove loading placeholder
          items.value = items.value.filter(m => m.id !== loadingMessageId.value)
          loadingMessageId.value = null

          streamingStore.startMessage(props.info.id)

          // Check if message already exists (SSE reconnect)
          if (!items.value.find(m => m.id === props.info.id)) {
            items.value.push({
              id: props.info.id,
              type: 'message',
              role: 'assistant',
              content: '',
              typing: true,
              loading: false,
              toolCalls: [],
            })
          }
          scrollToBottom()
        }
        break
      }

      case 'message.part.updated': {
        const part = props.part
        if (!part) break

        if (part.type === 'reasoning' && part.text) {
          items.value.push({
            id: Date.now().toString() + '-reasoning',
            type: 'reasoning',
            content: part.text,
            expanded: false,
          })
          scrollToBottom()
        } else if (part.type === 'text' && part.messageID === streamingStore.currentAssistantId) {
          streamingStore.applyPartUpdated(part)
          updateAssistantContent()
        } else if (part.type === 'tool') {
          // Handle tool call parts
          const assistantMsg = items.value.find(m => m.id === streamingStore.currentAssistantId)
          if (assistantMsg) {
            if (!assistantMsg.toolCalls) assistantMsg.toolCalls = []
            const idx = assistantMsg.toolCalls.findIndex(tc => tc.id === part.id)
            if (idx >= 0) {
              assistantMsg.toolCalls[idx] = part
            } else {
              assistantMsg.toolCalls.push(part)
            }
          }
        } else if (part.type === 'step-finish') {
          finalizeAssistantMessage(part.messageID)
        }
        break
      }

      case 'message.part.delta': {
        const { messageID, partID, delta } = props
        if (messageID === streamingStore.currentAssistantId) {
          streamingStore.applyPartDelta(messageID, partID, delta)
          updateAssistantContent()
        }
        break
      }
    }
  }

  function updateAssistantContent() {
    const streamingStore = useStreamingStore()
    const text = streamingStore.getStreamedText()
    const msg = items.value.find(m => m.id === streamingStore.currentAssistantId)
    if (msg) {
      msg.content = text
      scrollToBottom()
    }
  }

  function finalizeAssistantMessage(messageID) {
    const streamingStore = useStreamingStore()
    const targetId = messageID || streamingStore.currentAssistantId
    const msg = items.value.find(m => m.id === targetId)
    if (msg) {
      msg.typing = false
    }
    // Capture tool calls from streaming before finalizing
    if (msg && streamingStore.pendingToolCalls.length > 0) {
      if (!msg.toolCalls) msg.toolCalls = []
      for (const tc of streamingStore.pendingToolCalls) {
        if (!msg.toolCalls.find(t => t.id === tc.id)) {
          msg.toolCalls.push(tc)
        }
      }
    }
    streamingStore.finalizeMessage(messageID)
  }

  async function sendMessage(text, points, originalText) {
    const sessionStore = useSessionStore()
    if (!sessionStore.sessionId) {
      const created = await sessionStore.createSession()
      if (!created) {
        addSystemMessage('创建会话失败，请检查服务器连接')
        return false
      }
    }

    addUserMessage(text, points, originalText)
    setLoadingPlaceholder()

    try {
      const response = await fetch(`/session/${sessionStore.sessionId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent: 'gis-orchestrator',
          model: sessionStore.getModelConfig(),
          parts: [{ type: 'text', text }],
        }),
      })

      if (!response.ok) {
        const stillLoading = items.value.some(m => m.id === loadingMessageId.value)
        if (stillLoading) {
          items.value = items.value.filter(m => m.id !== loadingMessageId.value)
          loadingMessageId.value = null
          const errText = await response.text()
          addUserMessage(text, points)
          addSystemMessage(`请求失败: ${errText}`)
        }
      }
    } catch (error) {
      const stillLoading = items.value.some(m => m.id === loadingMessageId.value)
      if (stillLoading) {
        items.value = items.value.filter(m => m.id !== loadingMessageId.value)
        loadingMessageId.value = null
        addSystemMessage(`请求失败: ${error.message}`)
      }
    }
    return true
  }

  function clearAll() {
    items.value = []
    loadingMessageId.value = null
  }

  return {
    items,
    loadingMessageId,
    registerScroll,
    addSystemMessage,
    addUserMessage,
    setLoadingPlaceholder,
    applySSEEvent,
    sendMessage,
    clearAll,
  }
})
