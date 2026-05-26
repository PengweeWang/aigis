import { ref } from 'vue'
import { useEventCoalescing } from '../composables/opencode/useEventCoalescing.js'
import { useSSEConnection } from '../composables/opencode/useSSEConnection.js'
import { useMessageHandler } from '../composables/opencode/useMessageHandler.js'
import { useOpenCodeAPI } from '../composables/opencode/useOpenCodeAPI.js'

export function useOpenCodeChat(serverUrl = 'http://127.0.0.1:4096', options = {}) {
  const messages = ref([])
  const sessionBusy = ref(false)
  const selectedAgent = ref(options.defaultAgent || 'gis-orchestrator')
  const selectedModel = ref(options.defaultModel || '')
  const modelOptions = ref([])
  const agents = ref([])
  const currentSessionId = ref(null)
  const serverConnected = ref(false)
  const pendingQuestion = ref(null)
  const pendingPermission = ref(null)
  const todos = ref([])

  const messageHandler = useMessageHandler({
    messages,
    sessionBusy,
    currentSessionId,
  })

  // Wrap processEvent to handle question/permission/todo side effects
  function processEventWithSideEffects(payload) {
    const result = messageHandler.processEvent(payload)
    if (!result) return
    if (result.type === 'question') pendingQuestion.value = result.data
    else if (result.type === 'question-clear') {
      if (pendingQuestion.value && (result.data.requestID === pendingQuestion.value.id || result.data.requestID === pendingQuestion.value.requestID)) {
        pendingQuestion.value = null
      }
    }
    else if (result.type === 'permission') pendingPermission.value = result.data
    else if (result.type === 'permission-clear') {
      if (pendingPermission.value && (result.data.requestID === pendingPermission.value.id || result.data.requestID === pendingPermission.value.requestID)) {
        pendingPermission.value = null
      }
    }
    else if (result.type === 'todo') {
      if (result.data.todos) todos.value = result.data.todos
      else if (Array.isArray(result.data.items)) todos.value = result.data.items
    }
  }

  const { pushEvent, flushImmediate } = useEventCoalescing({
    processEvent: processEventWithSideEffects,
  })

  const { connectEventSource, disconnectEventSource } = useSSEConnection({
    serverUrl,
    pushEvent,
    flushImmediate,
  })

  const api = useOpenCodeAPI({
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
    addSystemMessage: messageHandler.addSystemMessage,
    addToolCallMsg: messageHandler.addToolCallMsg,
    clearSubSessionTracking: messageHandler.clearSubSessionTracking,
    setCommandSourceMap: messageHandler.setCommandSourceMap,
    subAgentNames: messageHandler.subAgentNames,
    subSessionIds: messageHandler.subSessionIds,
    onNewSession: options.onNewSession,
    defaultAgent: options.defaultAgent,
    defaultModel: options.defaultModel,
  })

  async function init() {
    connectEventSource()
    try {
      const r = await fetch(`${serverUrl}/global/health`)
      if (r.ok) {
        serverConnected.value = true
        messageHandler.addSystemMessage(`已连接至 OpenCode 服务器，版本: ${(await r.json()).version}`)
        await api.fetchAgents()
        await api.fetchCommands()
        await api.fetchModels()
        await api.createSession()
      } else {
        messageHandler.addSystemMessage('无法连接 OpenCode 服务器，请确保已运行 opencode serve')
      }
    } catch {
      messageHandler.addSystemMessage('无法连接 OpenCode 服务器，请确保已运行 opencode serve')
    }
  }

  function cleanup() {
    disconnectEventSource()
  }

  function setMessages(val) { messages.value = val }

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
    currentSessionId,
    todos,
    handleSend: api.handleSend,
    handleAbort: api.handleAbort,
    handleNewSession: api.handleNewSession,
    answerQuestion: api.answerQuestion,
    cancelQuestion: api.cancelQuestion,
    respondPermission: api.respondPermission,
    fetchSessionList: api.fetchSessionList,
    switchSession: api.switchSession,
    deleteSession: api.deleteSession,
    fetchTodos: api.fetchTodos,
    init,
    cleanup,
  }
}
