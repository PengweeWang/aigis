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
        <div v-if="msg.type === 'system'" class="msg-row system">
          <div class="system-msg">{{ msg.content }}</div>
        </div>

        <div v-else-if="msg.type === 'message'" class="msg-row" :class="msg.role">
          <div class="bubble" :class="msg.role" :data-loading="msg.loading || undefined">
            <template v-if="msg.role === 'user' && msg.points">
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
            <template v-else-if="msg.role === 'assistant'">
              <div v-if="msg.loading" class="loading-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
              <div v-else class="md-content" v-html="renderMarkdown(msg.content)" :data-typing="msg.typing || undefined"></div>
            </template>
            <template v-else>
              <div class="md-content" v-html="renderMarkdown(msg.content)"></div>
            </template>
          </div>
        </div>

        <details v-else-if="msg.type === 'reasoning'" class="thinking-block" :open="msg.expanded" @toggle="msg.expanded = $event.target.open">
          <summary>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
            <span>思考过程</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 9l6 6 6-6"/>
            </svg>
          </summary>
          <div class="thinking-content md-content" v-html="renderMarkdown(msg.content)"></div>
        </details>

        <div v-else-if="msg.type === 'tool_call'" class="tool-call-card" :class="msg.status">
          <div class="tool-call-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
            <span v-if="msg.agent" class="tool-agent-badge" :style="{ '--color': agentColor(msg.agent) }">{{ msg.agent }}</span>
             <span class="tool-call-name">{{ msg.subSessionId && msg.agent ? msg.agent : msg.toolName }}</span>
            <template v-if="!msg.subSessionId">
              <span class="tool-call-status" :class="msg.status">
                <span class="status-dot" :class="msg.status"></span>
                {{ statusLabel(msg.status) }}
              </span>
            </template>
            <span v-if="msg.subSessionId" class="sub-agent-indicator" :class="{ running: msg.subStatus === 'running' }">
              <span v-if="msg.subStatus === 'running'" class="sub-agent-spinner"></span>
              <span class="sub-agent-text">{{ msg._subStatusText || '等待中...' }}</span>
            </span>
            <button v-if="msg.input !== undefined || msg._subTools?.length || msg._subReasoning || msg._subText" class="tool-toggle" @click="msg._expanded = !msg._expanded">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                :style="{ transform: msg._expanded ? 'rotate(180deg)' : '' }">
                <path d="M6 9l6 6 6-6"/>
              </svg>
              {{ msg._expanded ? '收起' : '详情' }}
            </button>
          </div>
          <div v-if="msg._expanded" class="tool-call-body">
            <div v-if="msg.input !== undefined" class="tool-section">
              <div class="tool-section-label">输入</div>
              <pre class="tool-code">{{ formatToolInput(msg.input) }}</pre>
            </div>
            <div v-if="msg.output !== undefined && !msg._subTools?.length" class="tool-section">
              <div class="tool-section-label">输出</div>
              <pre class="tool-code">{{ truncateOutput(msg.output) }}</pre>
            </div>
            <div v-if="msg._subTools?.length" class="sub-tools">
              <div class="tool-section-label">子智能体调用</div>
              <div v-for="st in msg._subTools" :key="st.id" class="sub-tool-item" :class="st.status">
                <div class="sub-tool-header">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
                  </svg>
                  <span class="sub-tool-name">{{ st.tool }}</span>
                  <span class="tool-call-status" :class="st.status">
                    <span class="status-dot" :class="st.status"></span>
                    {{ statusLabel(st.status) }}
                  </span>
                  <button v-if="st.input !== undefined" class="tool-toggle" @click="st._expanded = !st._expanded">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                      :style="{ transform: st._expanded ? 'rotate(180deg)' : '' }">
                      <path d="M6 9l6 6 6-6"/>
                    </svg>
                    {{ st._expanded ? '收起' : '详情' }}
                  </button>
                </div>
                <div v-if="st._expanded" class="sub-tool-body">
                  <div v-if="st.input !== undefined" class="tool-section">
                    <div class="tool-section-label">输入</div>
                    <pre class="tool-code">{{ formatToolInput(st.input) }}</pre>
                  </div>
                  <div v-if="st.output !== undefined" class="tool-section">
                    <div class="tool-section-label">输出</div>
                    <pre class="tool-code">{{ truncateOutput(st.output) }}</pre>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="msg._subReasoning" class="sub-agent-response">
              <div class="tool-section-label">智能体思考</div>
              <div class="sub-reasoning">{{ msg._subReasoning }}</div>
            </div>
            <div v-if="msg._subText" class="sub-agent-response">
              <div class="tool-section-label">智能体回复</div>
              <div class="sub-text md-content" v-html="renderMarkdown(msg._subText)"></div>
            </div>
          </div>
          <div v-if="msg.subSessionId" class="sub-agent-bar">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
            </svg>
            <span>子智能体</span>
            <span class="sub-agent-status" :class="{ active: msg.subStatus === 'running' }">
              {{ msg.subStatus === 'running' ? '运行中...' : msg.subStatus === 'completed' ? '已完成' : '已结束' }}
            </span>
          </div>
        </div>

        <details v-else-if="msg.type === 'tool_chain'" class="thinking-block" :open="msg.expanded" @toggle="msg.expanded = $event.target.open">
          <summary>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            <span>工具调用链</span>
            <svg class="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 9l6 6 6-6"/>
            </svg>
          </summary>
          <div class="thought-chain">
            <div v-for="(step, i) in msg.steps" :key="i" class="chain-step" :class="step.status">
              <div class="chain-step-indicator">
                <span v-if="step.status === 'completed'" class="step-icon completed">✓</span>
                <span v-else-if="step.status === 'error'" class="step-icon error">✗</span>
                <span v-else-if="step.status === 'active'" class="step-icon active"></span>
                <span v-else class="step-icon pending"></span>
              </div>
              <div class="chain-step-body">
                <div class="chain-step-title">{{ step.title }}</div>
                <div v-if="step.content" class="chain-step-content">{{ step.content }}</div>
              </div>
            </div>
          </div>
        </details>
      </template>
    </div>

    <div v-if="pendingPermission" class="permission-dock">
      <div class="question-dock-header">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        <span>权限请求</span>
      </div>
      <div class="permission-dock-body">
        <div class="question-dock-text">{{ permissionLabel(pendingPermission.permission) }}</div>
        <div v-if="pendingPermission.patterns?.length" class="permission-patterns">
          <code v-for="(pat, i) in pendingPermission.patterns" :key="i" class="permission-pattern">{{ pat }}</code>
        </div>
      </div>
      <div class="question-dock-actions">
        <button class="q-btn q-btn-cancel" :disabled="permissionResponding" @click="doPermission('reject')">拒绝</button>
        <button class="q-btn q-btn-always" :disabled="permissionResponding" @click="doPermission('always')">始终允许</button>
        <button class="q-btn q-btn-submit" :disabled="permissionResponding" @click="doPermission('once')">允许一次</button>
      </div>
    </div>
    <div v-if="pendingQuestion && currentQuestion" class="question-dock">
      <div v-if="hasMultipleQuestions" class="question-dock-tabs">
        <button
          v-for="(_, ti) in pendingQuestion.questions"
          :key="ti"
          class="q-tab"
          :class="{ active: currentQuestionTab === ti }"
          @click="currentQuestionTab = ti"
        >{{ ti + 1 }}</button>
      </div>
      <div class="question-dock-header">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>
        </svg>
        <span>{{ currentQuestion.header || currentQuestion.question || '智能体需要确认' }}</span>
      </div>
      <div v-if="currentQuestion.question && currentQuestion.question !== currentQuestion.header" class="question-dock-text">{{ currentQuestion.question }}</div>
      <div v-if="currentQuestion.options?.length" class="question-dock-options">
        <button
          v-for="(opt, oi) in currentQuestion.options"
          :key="oi"
          class="question-option"
          :class="{ selected: selectedAnswer === opt.label }"
          @click="selectedAnswer = opt.label; showCustomInput = false"
        >
          <span class="q-radio" :class="{ checked: selectedAnswer === opt.label }"></span>
          <span class="q-label">{{ opt.label }}</span>
          <span v-if="opt.description" class="q-desc">{{ opt.description }}</span>
        </button>
        <button
          class="question-option"
          :class="{ selected: showCustomInput }"
          @click="showCustomInput = true; selectedAnswer = ''"
        >
          <span class="q-radio" :class="{ checked: showCustomInput }"></span>
          <span class="q-label">输入自定义答案</span>
          <span v-if="freeformAnswer" class="q-desc">{{ freeformAnswer }}</span>
        </button>
      </div>
      <div v-if="showCustomInput" class="question-dock-input">
        <textarea
          ref="questionTextareaRef"
          v-model="freeformAnswer"
          class="question-textarea"
          placeholder="输入回答..."
          rows="2"
          @input="resizeQuestionTextarea"
        ></textarea>
      </div>
      <div v-else-if="!currentQuestion.options?.length" class="question-dock-input">
        <textarea
          v-model="freeformAnswer"
          class="question-textarea"
          placeholder="输入回答..."
          rows="2"
        ></textarea>
      </div>
      <div class="question-dock-actions">
        <button class="q-btn q-btn-cancel" @click="cancelQuestion">取消</button>
        <button class="q-btn q-btn-submit" :disabled="!canSubmitAnswer" @click="submitAnswer">确认</button>
      </div>
    </div>
    <div class="chat-input-area">
      <div class="input-row">
          <div class="editor-wrapper">
            <div
              ref="textareaRef"
              class="chat-textarea"
              contenteditable="true"
              :class="{ disabled: sessionBusy }"
              role="textbox"
              aria-multiline="true"
              :aria-label="placeholder"
              @input="handleInput"
              @keydown.enter.exact.prevent="handleSend"
              @paste="handlePaste"
            ></div>
            <div v-if="!inputText.length" class="placeholder-text">{{ placeholder }}</div>
          <div class="editor-actions">
            <button v-if="!sessionBusy" class="send-btn" @click="handleSend" :disabled="!inputText.trim()">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 5v14M5 12l7 7 7-7"/>
              </svg>
            </button>
            <button v-else class="stop-btn" @click="apiAbort" title="停止回答">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
      <div v-if="agents.length > 1 || (showModelSelect && modelOptions.length > 0)" class="chat-selector-bar">
        <div v-if="agents.length > 1" class="selector-trigger" @click="agentOpen = !agentOpen" @blur="agentOpen = false" tabindex="0">
          <span class="selector-label truncate">{{ selectedAgentLabel || '选择智能体' }}</span>
          <svg class="selector-chevron" :class="{ open: agentOpen }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
          <div v-if="agentOpen" class="selector-dropdown">
            <div
              v-for="a in agents" :key="a.value"
              class="selector-option"
              :class="{ selected: selectedAgent === a.value }"
              :style="selectedAgent === a.value ? { color: a.color || '#6366f1' } : {}"
              @click.stop="selectAgent(a.value); agentOpen = false"
            >{{ a.label }}</div>
          </div>
        </div>
        <div v-if="showModelSelect && modelOptions.length > 0" class="selector-trigger model-selector" @click="modelOpen = !modelOpen" @blur="modelOpen = false" tabindex="0">
          <span class="selector-label truncate">{{ selectedModelLabel || '选择模型' }}</span>
          <svg class="selector-chevron" :class="{ open: modelOpen }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
          <div v-if="modelOpen" class="selector-dropdown">
            <template v-for="(models, group) in groupedModels" :key="group">
              <div v-if="group" class="selector-group-header">{{ group }}</div>
              <div
                v-for="m in models" :key="m.value"
                class="selector-option"
                :class="{ selected: selectedModel === m.value }"
                @click.stop="selectModel(m.value); modelOpen = false"
              >{{ m.name || m.label }}</div>
            </template>
          </div>
        </div>
        <div v-if="currentModelSupportsThinking" class="selector-trigger thinking-selector" @click="thinkingOpen = !thinkingOpen" @blur="thinkingOpen = false" tabindex="0">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
          </svg>
          <span class="selector-label">{{ thinkingEffortLabel }}</span>
          <svg class="selector-chevron" :class="{ open: thinkingOpen }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
          <div v-if="thinkingOpen" class="selector-dropdown">
            <div
              v-for="v in thinkingEffortVariants" :key="v"
              class="selector-option"
              :class="{ selected: thinkingEffort === v }"
              @click.stop="selectThinkingEffort(v); thinkingOpen = false"
            >{{ variantLabel(v) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div ref="bottomAnchorRef" class="scroll-anchor"></div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { useOpenCodeChat } from './useOpenCodeChat.js'

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
const textareaRef = ref(null)
const bottomAnchorRef = ref(null)

const VARIANT_LABELS = { low: '低', medium: '中', high: '高', xhigh: '最高' }
function variantLabel(v) { return VARIANT_LABELS[v] || v }
const inputText = ref('')
const thinkingEffort = ref('')
const agentOpen = ref(false)
const modelOpen = ref(false)
const thinkingOpen = ref(false)
const selectedAnswer = ref('')
const freeformAnswer = ref('')
const currentQuestionTab = ref(0)
const showCustomInput = ref(false)
const questionTextareaRef = ref(null)

function resizeQuestionTextarea() {
  const el = questionTextareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

watch(showCustomInput, (v) => {
  if (v) {
    nextTick(() => {
      const el = questionTextareaRef.value
      if (el) { el.focus(); resizeQuestionTextarea() }
    })
  }
})

const permissionResponding = ref(false)
const PERMISSION_LABELS = {
  read: '读取文件',
  write: '写入文件',
  command: '执行命令',
  glob: '搜索文件',
  edit: '编辑文件',
  apply_patch: '应用补丁',
  bash: '执行命令',
  webfetch: '访问网页',
}
function permissionLabel(name) {
  return PERMISSION_LABELS[name] || name || '执行操作'
}
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

const AGENT_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f97316', '#ef4444']
const agentColorMap = {}

function agentColor(name) {
  if (!name) return '#6366f1'
  if (!agentColorMap[name]) agentColorMap[name] = AGENT_COLORS[Object.keys(agentColorMap).length % AGENT_COLORS.length]
  return agentColorMap[name]
}

const TOOL_STATUS_LABELS = {
  running: '运行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

function statusLabel(s) {
  return TOOL_STATUS_LABELS[s] || s || '等待中'
}

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function selectAgent(value) {
  selectedAgent.value = value
}

function selectModel(value) {
  selectedModel.value = value
}

function selectThinkingEffort(value) {
  thinkingEffort.value = value
}

// --- Markdown renderer ---

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function renderMarkdown(text) {
  if (!text) return ''
  let html = escapeHtml(text)

  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const langClass = lang ? ` class="lang-${escapeHtml(lang)}"` : ''
    return `<pre${langClass}><code>${code}</code></pre>`
  })

  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/~~(.+?)~~/g, '<del>$1</del>')

  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')

  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')

  html = html.replace(/^---+\s*$/gm, '<hr>')

  html = html.replace(/^&gt; (.+)$/gm, '<blockquote><p>$1</p></blockquote>')
  html = html.replace(/<\/blockquote>\n<blockquote>/g, '\n')

  html = html.replace(/^\|(.+)\|\n\|[-| :]+\|\n(\|.+\|\n?)+/gm, (match) => {
    const rows = match.trim().split('\n')
    const headerCells = rows[0].slice(1, -1).split('|').map(c => c.trim())
    const bodyRows = rows.slice(2)
    let table = '<table>'
    table += '<thead><tr>' + headerCells.map(c => `<th>${c}</th>`).join('') + '</tr></thead>'
    if (bodyRows.length) {
      table += '<tbody>'
      for (const row of bodyRows) {
        const cells = row.slice(1, -1).split('|').map(c => c.trim())
        table += '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>'
      }
      table += '</tbody>'
    }
    table += '</table>'
    return table
  })

  const parts = html.split(/\n\n+/)
  html = parts.map(p => {
    p = p.trim()
    if (!p) return ''
    if (p.startsWith('<h') || p.startsWith('<pre') || p.startsWith('<ul') || p.startsWith('<ol') || p.startsWith('<table') || p.startsWith('<hr') || p.startsWith('<blockquote')) return p
    p = p.replace(/\n/g, '<br>')
    return `<p>${p}</p>`
  }).join('')

  return html
}

// --- UI ---

function handleInput() {
  const el = textareaRef.value
  if (!el) return
  inputText.value = el.textContent || ''
  el.style.height = 'auto'
  el.offsetHeight
  el.style.height = el.scrollHeight + 'px'
}

function handlePaste(e) {
  e.preventDefault()
  const text = (e.clipboardData || window.clipboardData).getData('text/plain')
  document.execCommand('insertText', false, text)
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

function handleSend() {
  const text = inputText.value
  if (sessionBusy.value || !text.trim()) return
  inputText.value = ''
  if (textareaRef.value) { textareaRef.value.innerHTML = ''; textareaRef.value.style.height = 'auto' }
  apiSend({ text, agent: selectedAgent.value, model: selectedModel.value, thinkingEffort: thinkingEffort.value })
}

async function handleNewSession() {
  await apiNewSession()
  emit('new-session')
}

function formatToolInput(input) {
  if (typeof input === 'string') return input
  try { return JSON.stringify(input, null, 2) } catch { return String(input) }
}

function truncateOutput(out) {
  if (!out) return ''
  const s = typeof out === 'string' ? out : JSON.stringify(out, null, 2)
  return s.length > 2000 ? s.slice(0, 2000) + '\n... (已截断)' : s
}

// scroll when messages change
watch(() => messages.value?.length, () => scrollToBottom())

onMounted(() => init())
onUnmounted(() => cleanup())

defineExpose({
  scrollToBottom,
  scrollToTop,
})
</script>

<style scoped>
/* === Panel === */
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

/* === Header === */
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

/* === Selector Bar (agent + model) === */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chat-selector-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-top: 6px;
  min-height: 28px;
}
.selector-trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
  outline: none;
  max-width: 160px;
  transition: background 0.15s;
}
.selector-trigger.model-selector {
  max-width: 240px;
}
.selector-trigger.thinking-selector {
  max-width: 120px;
}
.selector-trigger:hover {
  background: rgba(0,0,0,0.04);
}
.selector-label {
  color: #666;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.3;
}
.selector-chevron {
  flex-shrink: 0;
  color: #999;
  transition: transform 0.2s;
}
.selector-chevron.open {
  transform: rotate(180deg);
}
.selector-dropdown {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 0;
  min-width: 180px;
  max-height: 200px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  z-index: 100;
  padding: 4px;
}
.selector-group-header {
  padding: 6px 10px 3px;
  font-size: 10px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.selector-group-header:not(:first-child) {
  margin-top: 4px;
  border-top: 1px solid #f0f0f0;
  padding-top: 8px;
}
.selector-option {
  padding: 6px 10px;
  border-radius: 5px;
  font-size: 12px;
  color: #444;
  cursor: pointer;
  transition: background 0.1s;
}
.selector-option:hover {
  background: #f0f5ff;
}
.selector-option.selected {
  font-weight: 600;
}

/* === Messages === */
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

.msg-row {
  display: flex;
  animation: msgFadeIn 0.2s ease;
}
@keyframes msgFadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
.msg-row.assistant {
  justify-content: flex-start;
}
.msg-row.user {
  justify-content: flex-end;
}
.msg-row.system {
  justify-content: center;
}

/* === Bubbles === */
.bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.55;
  word-break: break-word;
}
.bubble.assistant {
  background: #fff;
  color: #1a1a2e;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.bubble.user {
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.25);
}
.bubble.user .points-card {
  --text-color: #1a5cc8;
  --bg-color: #f0f5ff;
}
.bubble.user .user-text {
  color: #fff;
}
.bubble[data-loading] {
  display: flex;
  align-items: center;
  min-height: 36px;
  background: #fff;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
}
.loading-indicator .dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #bbb;
  animation: dotBounce 1.4s infinite ease-in-out;
}
.loading-indicator .dot:nth-child(1) { animation-delay: 0s; }
.loading-indicator .dot:nth-child(2) { animation-delay: 0.16s; }
.loading-indicator .dot:nth-child(3) { animation-delay: 0.32s; }
@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* === Markdown content === */
.md-content {
  font-size: 13px;
  line-height: 1.6;
}
.md-content :deep(p) { margin: 0 0 8px; }
.md-content :deep(p:last-child) { margin-bottom: 0; }
.md-content :deep(h1) { font-size: 18px; margin: 14px 0 8px; font-weight: 700; color: #1a1a2e; }
.md-content :deep(h2) { font-size: 16px; margin: 12px 0 6px; font-weight: 700; color: #1a1a2e; }
.md-content :deep(h3) { font-size: 14px; margin: 10px 0 4px; font-weight: 600; color: #1a1a2e; }
.md-content :deep(h4) { font-size: 13px; margin: 8px 0 4px; font-weight: 600; color: #333; }
.md-content :deep(code) {
  font-size: 12px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
  background: rgba(0,0,0,0.06);
  padding: 2px 5px;
  border-radius: 4px;
  color: #e74c3c;
}
.md-content :deep(pre) {
  background: #1a1a2e;
  border-radius: 8px;
  padding: 12px 14px;
  overflow-x: auto;
  margin: 10px 0;
}
.md-content :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #e8e8e8;
}
.md-content :deep(ul), .md-content :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}
.md-content :deep(li) { margin: 3px 0; }
.md-content :deep(a) { color: #1890ff; text-decoration: none; }
.md-content :deep(a:hover) { text-decoration: underline; }
.md-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 12px;
  border-radius: 8px;
  overflow: hidden;
}
.md-content :deep(th), .md-content :deep(td) {
  border: 1px solid #e8e8e8;
  padding: 8px 12px;
  text-align: left;
}
.md-content :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
  color: #333;
}
.md-content :deep(tbody tr:nth-child(even)) {
  background: #fafbfc;
}
.md-content :deep(hr) {
  border: none;
  border-top: 1px solid #e8e8e8;
  margin: 14px 0;
}
.md-content :deep(blockquote) {
  margin: 8px 0;
  padding: 6px 14px;
  border-left: 3px solid #d0d5dd;
  color: #666;
  font-size: 12px;
  background: #f8f9fa;
  border-radius: 0 6px 6px 0;
}
.md-content :deep(strong) { font-weight: 600; color: #1a1a2e; }
.md-content :deep(del) { text-decoration: line-through; color: #999; }
.md-content :deep(br) { content: ''; display: block; margin: 4px 0; }

.md-content[data-typing]::after {
  content: '|';
  display: inline;
  animation: cursorBlink 0.8s step-end infinite;
  color: #1890ff;
  font-weight: 500;
}
@keyframes cursorBlink {
  50% { opacity: 0; }
}

.user-text {
  font-size: 13px;
  line-height: 1.5;
}

/* === System message === */
.system-msg {
  width: 100%;
  text-align: center;
  font-size: 11px;
  color: #999;
  padding: 4px 0;
}

/* === Points card === */
.points-card {
  background: linear-gradient(135deg, #f0f5ff, #e8f0fe);
  border: 1px solid #d6e4ff;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 8px;
}
.points-card-header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  background: rgba(24, 144, 255, 0.08);
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
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: 9px;
  padding: 0 5px;
}
.points-card-body { padding: 6px 10px; }
.point-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  font-size: 11px;
}
.point-item + .point-item { border-top: 1px solid #e6f0ff; }
.point-label {
  width: 22px; height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(24, 144, 255, 0.3);
}
.point-coords {
  color: #666;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 10px;
}

/* === Thinking block === */
.thinking-block {
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.thinking-block summary {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 14px;
  font-size: 12px;
  font-weight: 600;
  color: #555;
  cursor: pointer;
  user-select: none;
  background: #fafbfc;
  transition: background 0.15s;
}
.thinking-block summary:hover {
  background: #f5f7fa;
}
.thinking-block summary .chevron {
  margin-left: auto;
  transition: transform 0.2s;
  color: #bbb;
}
.thinking-block[open] summary .chevron {
  transform: rotate(180deg);
}
.thinking-block[open] summary {
  border-bottom: 1px solid #f0f0f0;
}
.thinking-content {
  padding: 0 14px 14px;
  font-size: 12px;
  color: #666;
  line-height: 1.6;
}
.thinking-content :deep(p) { font-size: 12px; }

/* === Thought chain === */
.thought-chain {
  padding: 10px 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.chain-step {
  display: flex;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #f8f9fa;
  font-size: 12px;
  transition: background 0.15s;
}
.chain-step:hover {
  background: #f0f2f5;
}
.chain-step-indicator {
  flex-shrink: 0;
  width: 20px;
  display: flex;
  justify-content: center;
  padding-top: 2px;
}
.step-icon {
  width: 16px; height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
}
.step-icon.completed { background: #52c41a; color: #fff; }
.step-icon.error { background: #ff4d4f; color: #fff; }
.step-icon.active {
  background: #1890ff;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.2);
  animation: pulse 1.5s infinite;
}
.step-icon.pending {
  background: #d9d9d9;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.chain-step-body { flex: 1; }
.chain-step-title { font-weight: 600; color: #333; }
.chain-step-content { color: #888; font-size: 11px; margin-top: 3px; }

/* === Tool call card === */
.tool-call-card {
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.tool-call-card.completed { border-left: 3px solid #52c41a; }
.tool-call-card.failed { border-left: 3px solid #ff4d4f; }
.tool-call-card.running { border-left: 3px solid #1890ff; }
.tool-call-card.cancelled { border-left: 3px solid #d9d9d9; }

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 12px;
  font-size: 11px;
  color: #555;
  background: #fafbfc;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.15s;
}
.tool-agent-badge {
  font-size: 10px;
  font-weight: 600;
  color: var(--color, #6366f1);
  background: color-mix(in srgb, var(--color, #6366f1) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--color, #6366f1) 20%, transparent);
  border-radius: 4px;
  padding: 1px 7px;
  white-space: nowrap;
}
.tool-call-name {
  font-weight: 600;
  color: #333;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 11px;
}
.tool-call-status {
  margin-left: auto;
  font-size: 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #888;
}
.tool-call-status.completed { color: #52c41a; }
.tool-call-status.failed { color: #ff4d4f; }
.tool-call-status.running { color: #1890ff; }
.tool-call-status.cancelled { color: #999; }

.sub-agent-indicator {
  font-size: 10px;
  display: flex;
  align-items: center;
  gap: 3px;
  color: #888;
  white-space: nowrap;
}
.sub-agent-indicator.running {
  color: #1890ff;
}
.sub-agent-spinner {
  width: 8px;
  height: 8px;
  border: 1.5px solid #1890ff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  display: inline-block;
}
.status-dot.running { background: #1890ff; animation: pulse 1.5s infinite; }
.status-dot.completed { background: #52c41a; }
.status-dot.failed { background: #ff4d4f; }
.status-dot.cancelled { background: #d9d9d9; }

.tool-toggle {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  padding: 3px 6px;
  border-radius: 5px;
  transition: all 0.15s;
}
.tool-toggle:hover { background: #e8e8e8; color: #555; }

.tool-call-body {
  padding: 10px 12px;
  background: #fafbfc;
}
.tool-section { margin-bottom: 8px; }
.tool-section:last-child { margin-bottom: 0; }
.tool-section-label {
  font-size: 10px;
  font-weight: 600;
  color: #999;
  margin-bottom: 5px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.tool-code {
  font-size: 10px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 8px 10px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  color: #444;
  line-height: 1.5;
  max-height: 150px;
  overflow-y: auto;
}
.sub-tools {
  margin-top: 10px;
  border-top: 1px solid #e8e8e8;
  padding-top: 8px;
}
.sub-tool-item {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  margin-top: 6px;
  overflow: hidden;
  background: #fafbfc;
}
.sub-tool-item.completed { border-left: 2px solid #52c41a; }
.sub-tool-item.failed { border-left: 2px solid #ff4d4f; }
.sub-tool-item.running { border-left: 2px solid #1890ff; }
.sub-tool-header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 8px;
  font-size: 10px;
  color: #555;
  background: #f5f7fa;
}
.sub-tool-name {
  font-weight: 600;
  color: #333;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 10px;
}
.sub-tool-body {
  padding: 6px 8px;
}
.sub-agent-response {
  margin-top: 8px;
}
.sub-reasoning {
  font-size: 11px;
  color: #666;
  background: #f5f7fa;
  border-radius: 6px;
  padding: 8px 10px;
  line-height: 1.5;
  white-space: pre-wrap;
}
.sub-text {
  font-size: 12px;
  line-height: 1.5;
  background: #f8faff;
  border: 1px solid #e0e7ff;
  border-radius: 6px;
  padding: 8px 10px;
}

.sub-agent-bar {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #f0f5ff, #e8f0fe);
  border-top: 1px solid #d6e4ff;
  font-size: 10px;
  color: #1a5cc8;
}
.sub-agent-status {
  margin-left: auto;
  font-size: 10px;
  color: #888;
}
.sub-agent-status.active { color: #1890ff; }

/* === Permission dock === */
.permission-dock {
  padding: 12px 14px;
  border-top: 1px solid #e8e8e8;
  background: linear-gradient(135deg, #fff5f5, #fff0f0);
}
.permission-dock-body {
  margin-bottom: 8px;
}
.permission-dock-hint {
  font-size: 12px;
  color: #555;
  margin-bottom: 6px;
}
.permission-patterns {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.permission-pattern {
  font-size: 11px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  background: rgba(0,0,0,0.05);
  padding: 3px 8px;
  border-radius: 4px;
  color: #cf1322;
  word-break: break-all;
}
.q-btn-always {
  background: #f0f0f0;
  color: #555;
}
.q-btn-always:hover {
  background: #e4e4e4;
}

/* === Question dock === */
.question-dock {
  padding: 12px 14px;
  border-top: 1px solid #e8e8e8;
  background: linear-gradient(135deg, #fefcf5, #fef9e7);
}
.question-dock-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #d48806;
  margin-bottom: 8px;
}
.question-dock-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}
.q-tab {
  width: 24px; height: 24px;
  border-radius: 50%;
  border: 1px solid #e8e8e8;
  background: #fff;
  color: #999;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.q-tab.active { background: #d48806; color: #fff; border-color: #d48806; }
.q-tab:hover:not(.active) { border-color: #f0c040; }
.question-dock-text {
  font-size: 11px;
  color: #666;
  margin-bottom: 8px;
  line-height: 1.5;
}
.question-dock-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}
.question-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
  font-size: 12px;
}
.question-option:hover { border-color: #f0c040; background: #fffef5; }
.question-option.selected { border-color: #d48806; background: #fff8e1; }
.q-radio {
  width: 14px; height: 14px;
  border-radius: 50%;
  border: 2px solid #d9d9d9;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}
.q-radio.checked { border-color: #d48806; }
.q-radio.checked::after {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #d48806;
}
.q-label { font-weight: 500; color: #333; }
.q-desc { color: #999; font-size: 11px; }
.question-dock-input { margin-bottom: 8px; }
.question-textarea {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  font-family: inherit;
  outline: none;
  resize: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.question-textarea:focus { border-color: #d48806; box-shadow: 0 0 0 2px rgba(212, 136, 6, 0.1); }
.question-dock-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}
.q-btn {
  padding: 6px 14px;
  border-radius: 6px;
  border: none;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.q-btn-cancel { background: #f0f0f0; color: #666; }
.q-btn-cancel:hover { background: #e4e4e4; }
.q-btn-submit { background: #d48806; color: #fff; }
.q-btn-submit:hover { background: #e8a020; }
.q-btn-submit:disabled { background: #d9d9d9; color: #fff; cursor: not-allowed; }

/* === Input area === */
.chat-input-area {
  padding: 8px 14px 10px;
  border-top: 1px solid #f0f0f0;
  background: #fff;
}
.input-row {
  display: flex;
  align-items: flex-end;
}
.editor-wrapper {
  position: relative;
  flex: 1;
  display: flex;
}
.chat-textarea {
  flex: 1;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 9px 36px 9px 14px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  min-height: 38px;
  line-height: 1.45;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: #fafbfc;
  white-space: pre-wrap;
  overflow: hidden;
  word-break: break-word;
}
.chat-textarea:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.08);
  background: #fff;
}
.chat-textarea.disabled {
  background: #f5f5f5;
  color: #999;
  border-color: #e8e8e8;
  pointer-events: none;
}
.chat-textarea:empty:before {
  content: attr(data-placeholder);
  color: #bbb;
  pointer-events: none;
}
.placeholder-text {
  position: absolute;
  top: 9px;
  left: 14px;
  right: 36px;
  font-size: 13px;
  color: #bbb;
  pointer-events: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.editor-actions {
  position: absolute;
  bottom: 4px;
  right: 4px;
  display: flex;
  align-items: center;
}
.send-btn, .stop-btn {
  width: 28px; height: 28px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s ease;
}
.send-btn {
  background: #1890ff;
  color: #fff;
}
.send-btn:hover:not(:disabled) {
  background: #40a9ff;
}
.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}
.send-btn:disabled { background: #d9d9d9; color: #fff; cursor: not-allowed; }
.stop-btn {
  background: #ff4d4f;
  color: #fff;
}
.stop-btn:hover {
  background: #ff7875;
}


.scroll-anchor { height: 0; }
</style>
