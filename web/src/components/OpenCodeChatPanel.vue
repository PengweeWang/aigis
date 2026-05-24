<template>
  <div class="ai-chat-panel" :style="{ width: panelWidth + 'px' }">
    <div class="resize-handle" @mousedown="startResize"></div>

    <div class="chat-header">
      <slot name="header-title">
        <h3>{{ title }}</h3>
      </slot>
      <div class="header-actions">
        <slot name="header-actions">
          <button v-if="showSessionHistory" class="icon-btn new-session-btn" @click="toggleSessionList" title="历史会话">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 8v4l3 3"/>
              <circle cx="12" cy="12" r="9"/>
            </svg>
          </button>
          <button v-if="showNewSession" class="icon-btn new-session-btn" @click="handleNewSession" title="新建会话">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </slot>
      </div>
    </div>

    <div class="chat-messages" ref="messagesRef">
      <template v-for="msg in messages" :key="msg.id">
        <ChatMessage v-if="msg.type === 'system' || msg.type === 'message'" :msg="msg" />
        <ThinkingBlock v-else-if="msg.type === 'reasoning'" :msg="msg" />
        <ToolCallCard v-else-if="msg.type === 'tool_call'" :msg="msg" />
        <ToolChain v-else-if="msg.type === 'tool_chain'" :msg="msg" />
      </template>
    </div>

    <TodoList v-if="todos.length > 0" :todos="todos" />

    <PermissionDock
      v-if="pendingPermission"
      :permission="pendingPermission"
      :responding="permissionResponding"
      @respond="doPermission"
    />
    <QuestionDock
      v-if="pendingQuestion && currentQuestion"
      :questions="pendingQuestion.questions || [pendingQuestion]"
      :currentQuestion="currentQuestion"
      :hasMultipleQuestions="hasMultipleQuestions"
      :currentTab="currentQuestionTab"
      :selectedAnswer="selectedAnswer"
      :freeformAnswer="freeformAnswer"
      :showCustomInput="showCustomInput"
      :canSubmit="canSubmitAnswer"
      @update:currentTab="currentQuestionTab = $event"
      @select-option="selectedAnswer = $event; showCustomInput = false"
      @select-custom="showCustomInput = true; selectedAnswer = ''"
      @update:freeformAnswer="freeformAnswer = $event"
      @cancel="cancelQuestion"
      @submit="submitAnswer"
    />
    <ChatInput
      ref="chatInputRef"
      :placeholder="placeholder"
      :sessionBusy="sessionBusy"
      :inputText="inputText"
      :showModelSelect="showModelSelect"
      :agents="agents"
      :modelOptions="modelOptions"
      :selectedAgent="selectedAgent"
      :selectedModel="selectedModel"
      :selectedAgentLabel="selectedAgentLabel"
      :selectedModelLabel="selectedModelLabel"
      :currentModelSupportsThinking="currentModelSupportsThinking"
      :thinkingEffort="thinkingEffort"
      :thinkingEffortLabel="thinkingEffortLabel"
      :thinkingEffortVariants="thinkingEffortVariants"
      :groupedModels="groupedModels"
      @update:inputText="inputText = $event"
      @send="handleSend"
      @abort="apiAbort"
      @select-agent="selectAgent"
      @select-model="selectModel"
      @select-thinking-effort="selectThinkingEffort"
    >
      <template #toolbar>
        <slot name="input-toolbar"></slot>
      </template>
      <template #toolbar-right>
        <slot name="input-toolbar-right"></slot>
      </template>
    </ChatInput>

    <SessionList
      v-if="showSessionList"
      :sessions="sessionListData"
      :currentSessionId="currentSessionId"
      :loading="sessionListLoading"
      @close="showSessionList = false"
      @switch="handleSwitchSession"
      @delete="handleDeleteSession"
    />

    <div ref="bottomAnchorRef" class="scroll-anchor"></div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { useOpenCodeChat } from './useOpenCodeChat.js'
import { variantLabel } from './opencode/utils.js'
import ChatMessage from './opencode/ChatMessage.vue'
import ThinkingBlock from './opencode/ThinkingBlock.vue'
import ToolCallCard from './opencode/ToolCallCard.vue'
import ToolChain from './opencode/ToolChain.vue'
import PermissionDock from './opencode/PermissionDock.vue'
import QuestionDock from './opencode/QuestionDock.vue'
import ChatInput from './opencode/ChatInput.vue'
import SessionList from './opencode/SessionList.vue'
import TodoList from './opencode/TodoList.vue'

const props = defineProps({
  title: { type: String, default: 'AI Chat' },
  serverUrl: { type: String, default: 'http://127.0.0.1:4096' },
  panelWidth: { type: Number, default: 280 },
  minPanelWidth: { type: Number, default: 200 },
  placeholder: { type: String, default: '请输入您的问题...' },
  showModelSelect: { type: Boolean, default: true },
  showNewSession: { type: Boolean, default: true },
  showSessionHistory: { type: Boolean, default: true },
  defaultAgent: { type: String, default: '' },
  defaultModel: { type: String, default: '' },
  getAnnotationPoints: { type: Function, default: null },
  onNewSession: { type: Function, default: null },
})

const emit = defineEmits([
  'update:panelWidth',
  'new-session',
])

const {
  messages,
  sessionBusy,
  selectedAgent,
  selectedModel,
  modelOptions,
  agents,
  pendingQuestion,
  pendingPermission,
  currentSessionId,
  todos,
  handleSend: apiSend,
  handleAbort: apiAbort,
  handleNewSession: apiNewSession,
  answerQuestion,
  cancelQuestion: apiCancelQuestion,
  respondPermission,
  fetchSessionList,
  switchSession: apiSwitchSession,
  deleteSession: apiDeleteSession,
  fetchTodos,
  init,
  cleanup,
} = useOpenCodeChat(props.serverUrl, { defaultAgent: props.defaultAgent, defaultModel: props.defaultModel, onNewSession: props.onNewSession })

const messagesRef = ref(null)
const bottomAnchorRef = ref(null)
const chatInputRef = ref(null)

const inputText = ref('')
const thinkingEffort = ref('')
const selectedAnswer = ref('')
const freeformAnswer = ref('')
const currentQuestionTab = ref(0)
const showCustomInput = ref(false)
const permissionResponding = ref(false)
const showSessionList = ref(false)
const sessionListData = ref([])
const sessionListLoading = ref(false)

watch(showCustomInput, (v) => {
  if (v) {
    nextTick(() => {
      const el = chatInputRef.value?.questionTextareaRef
      if (el) { el.focus() }
    })
  }
})

async function doPermission(response) {
  if (permissionResponding.value) return
  permissionResponding.value = true
  await respondPermission(response)
  permissionResponding.value = false
}

const canSubmitAnswer = computed(() => {
  const q = currentQuestion.value
  if (!q) return false
  if (q.options?.length && !showCustomInput.value) return !!selectedAnswer.value
  return freeformAnswer.value.trim().length > 0
})

function submitAnswer() {
  if (!canSubmitAnswer.value) return
  const questions = pendingQuestion.value?.questions || [pendingQuestion.value]
  const answers = questions.map((q, i) => {
    if (currentQuestionTab.value === i) {
      if (q.options?.length && !showCustomInput.value) return [selectedAnswer.value]
      return [freeformAnswer.value.trim()]
    }
    return []
  })
  answerQuestion(answers)
  selectedAnswer.value = ''
  freeformAnswer.value = ''
  currentQuestionTab.value = 0
  showCustomInput.value = false
}

function cancelQuestion() {
  apiCancelQuestion()
  selectedAnswer.value = ''
  freeformAnswer.value = ''
  currentQuestionTab.value = 0
  showCustomInput.value = false
}

const currentQuestion = computed(() => {
  if (!pendingQuestion.value) return null
  const questions = pendingQuestion.value.questions || [pendingQuestion.value]
  return questions[currentQuestionTab.value] || questions[0]
})

const hasMultipleQuestions = computed(() => {
  return !!(pendingQuestion.value?.questions?.length > 1)
})

const selectedAgentLabel = computed(() => agents.value.find(a => a.value === selectedAgent.value)?.label || '')
const selectedModelLabel = computed(() => {
  const m = modelOptions.value.find(m => m.value === selectedModel.value)
  return m?.name || m?.label || ''
})
const currentModelSupportsThinking = computed(() => {
  const m = modelOptions.value.find(m => m.value === selectedModel.value)
  return m?.variants && m.variants.length > 0
})
const thinkingEffortLabel = computed(() => {
  const m = modelOptions.value.find(m => m.value === selectedModel.value)
  if (!m?.variants?.length) return ''
  if (!thinkingEffort.value) return '思考强度'
  return variantLabel(thinkingEffort.value)
})
const thinkingEffortVariants = computed(() => {
  const m = modelOptions.value.find(m => m.value === selectedModel.value)
  return m?.variants || []
})
const groupedModels = computed(() => {
  const groups = {}
  for (const m of modelOptions.value) {
    const key = m.group || ''
    if (!groups[key]) groups[key] = []
    groups[key].push(m)
  }
  return groups
})

watch(selectedModel, (v) => {
  if (!thinkingEffort.value) {
    const m = modelOptions.value.find(m => m.value === v)
    if (m?.variants?.length) thinkingEffort.value = m.variants[0]
  }
})

function selectAgent(value) {
  selectedAgent.value = value
}

function selectModel(value) {
  selectedModel.value = value
}

function selectThinkingEffort(value) {
  thinkingEffort.value = value
}

async function toggleSessionList() {
  if (showSessionList.value) {
    showSessionList.value = false
    return
  }
  sessionListLoading.value = true
  showSessionList.value = true
  sessionListData.value = await fetchSessionList()
  sessionListLoading.value = false
}

async function handleSwitchSession(sessionId) {
  const ok = await apiSwitchSession(sessionId)
  if (ok) {
    showSessionList.value = false
    await fetchTodos()
  }
}

async function handleDeleteSession(sessionId) {
  const ok = await apiDeleteSession(sessionId)
  if (ok) {
    sessionListData.value = sessionListData.value.filter(s => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      await handleNewSession()
    }
  }
}

function handleSend() {
  const text = inputText.value
  if (sessionBusy.value || !text.trim()) return
  inputText.value = ''
  chatInputRef.value?.clear()
  const points = props.getAnnotationPoints ? props.getAnnotationPoints() : []
  apiSend({ text, agent: selectedAgent.value, model: selectedModel.value, thinkingEffort: thinkingEffort.value, points })
}

async function handleNewSession() {
  await apiNewSession()
  emit('new-session')
}

function startResize(e) {
  const startX = e.clientX
  const startW = props.panelWidth
  function onMove(ev) {
    emit('update:panelWidth', Math.max(props.minPanelWidth, Math.min(800, startW + ev.clientX - startX)))
  }
  function onUp() {
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

watch(() => messages.value?.length, () => scrollToBottom())

onMounted(() => init())
onUnmounted(() => cleanup())

defineExpose({
  scrollToBottom,
  scrollToTop,
})
</script>

<style scoped>
.ai-chat-panel {
  --panel-bg: #ffffff;
  --panel-border: rgba(0, 0, 0, 0.06);
  --header-bg-from: #fafbfc;
  --header-bg-to: #f7f8fa;
  --header-border: #eef0f2;
  --header-title-from: #1e1b4b;
  --header-title-to: #312e81;
  --icon-btn-bg: #f1f3f5;
  --icon-btn-hover-bg: #e5e8eb;
  --icon-btn-color: #555;
  --icon-active-from: #4f46e5;
  --icon-active-to: #6366f1;
  --icon-active-shadow: rgba(79, 70, 229, 0.35);
  --msg-bg: #f9fafb;
  --scrollbar-thumb: rgba(0, 0, 0, 0.12);
  --scrollbar-track: transparent;
  --panel-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 2px 12px rgba(0, 0, 0, 0.04);

  position: relative;
  height: 100%;
  background: var(--panel-bg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: none;
  box-shadow: var(--panel-shadow);
  user-select: none;
}
.resize-handle {
  position: absolute;
  right: -2px; top: 0; bottom: 0;
  width: 8px;
  cursor: col-resize;
  z-index: 20;
  background: transparent;
  transition: background 0.2s;
}
.resize-handle:hover,
.resize-handle:active {
  background: rgba(79, 70, 229, 0.12);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--header-border);
  background: linear-gradient(180deg, var(--header-bg-from) 0%, var(--header-bg-to) 100%);
  flex-shrink: 0;
}
.chat-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--header-title-from), var(--header-title-to));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.3px;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.new-session-btn {
  width: 32px; height: 32px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--icon-btn-bg);
  color: var(--icon-btn-color);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0;
}
.icon-btn:hover {
  background: var(--icon-btn-hover-bg);
  color: #333;
  transform: translateY(-1px);
}
.icon-btn:active {
  transform: translateY(0) scale(0.96);
}
.icon-btn.active {
  background: linear-gradient(135deg, var(--icon-active-from), var(--icon-active-to)) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px var(--icon-active-shadow), 0 1px 3px rgba(0, 0, 0, 0.1);
}
.icon-btn:focus-visible {
  outline: 2px solid var(--icon-active-from);
  outline-offset: 2px;
}
.new-session-btn {
  background: var(--icon-btn-bg) !important;
}
.new-session-btn:hover {
  background: var(--icon-btn-hover-bg) !important;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  background: var(--msg-bg);
  scroll-behavior: smooth;
}
.chat-messages::-webkit-scrollbar {
  width: 5px;
}
.chat-messages::-webkit-scrollbar-track {
  background: var(--scrollbar-track);
}
.chat-messages::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 3px;
}
.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.22);
}
.chat-messages > * {
  flex-shrink: 0;
}

.scroll-anchor { height: 0; }
</style>
