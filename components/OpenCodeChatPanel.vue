<template>
  <div class="ai-chat-panel" :style="{ width: panelWidth + 'px' }">
    <div class="resize-handle" @mousedown="startResize"></div>

    <div class="chat-header">
      <slot name="header-title">
        <h3>{{ title }}</h3>
      </slot>
      <div class="header-actions">
        <slot name="header-actions">
          <div v-if="showPointAdd" class="add-point-wrapper">
            <button class="icon-btn" :class="{ active: pointAddMode }" @click="$emit('toggle-point-add')" :title="pointAddMode ? '关闭标注模式' : '开启标注模式'">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" :stroke="pointAddMode ? '#fff' : 'currentColor'" stroke-width="2">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                <circle cx="12" cy="9" r="2.5"/>
              </svg>
            </button>
            <span v-if="userPointsCount > 0" class="point-badge">{{ userPointsCount }}</span>
          </div>
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

const props = defineProps({
  title: { type: String, default: 'AI Chat' },
  serverUrl: { type: String, default: 'http://127.0.0.1:4096' },
  panelWidth: { type: Number, default: 280 },
  minPanelWidth: { type: Number, default: 200 },
  placeholder: { type: String, default: '请输入您的问题...' },
  showModelSelect: { type: Boolean, default: true },
  showNewSession: { type: Boolean, default: true },
  showPointAdd: { type: Boolean, default: false },
  pointAddMode: { type: Boolean, default: false },
  userPointsCount: { type: Number, default: 0 },
})

const emit = defineEmits([
  'toggle-point-add',
  'update:panelWidth',
  'update:pointAddMode',
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
  handleSend: apiSend,
  handleAbort: apiAbort,
  handleNewSession: apiNewSession,
  answerQuestion,
  cancelQuestion: apiCancelQuestion,
  respondPermission,
  init,
  cleanup,
} = useOpenCodeChat(props.serverUrl)

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

function handleSend() {
  const text = inputText.value
  if (sessionBusy.value || !text.trim()) return
  inputText.value = ''
  chatInputRef.value?.clear()
  apiSend({ text, agent: selectedAgent.value, model: selectedModel.value, thinkingEffort: thinkingEffort.value })
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
  position: relative;
  height: 100%;
  background: #fff;
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

.scroll-anchor { height: 0; }
</style>
