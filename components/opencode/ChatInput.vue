<template>
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
          @keydown.enter.exact.prevent="$emit('send')"
          @paste="handlePaste"
        ></div>
        <div v-if="!inputText.length" class="placeholder-text">{{ placeholder }}</div>
        <div class="editor-actions">
          <button v-if="!sessionBusy" class="send-btn" @click="$emit('send')" :disabled="!inputText.trim()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 5v14M5 12l7 7 7-7"/>
            </svg>
          </button>
          <button v-else class="stop-btn" @click="$emit('abort')" title="停止回答">
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
            @click.stop="$emit('select-agent', a.value); agentOpen = false"
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
              @click.stop="$emit('select-model', m.value); modelOpen = false"
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
            @click.stop="$emit('select-thinking-effort', v); thinkingOpen = false"
          >{{ variantLabel(v) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { variantLabel } from './utils.js'

const props = defineProps({
  placeholder: { type: String, default: '请输入您的问题...' },
  sessionBusy: { type: Boolean, default: false },
  inputText: { type: String, default: '' },
  showModelSelect: { type: Boolean, default: true },
  agents: { type: Array, default: () => [] },
  modelOptions: { type: Array, default: () => [] },
  selectedAgent: { type: String, default: '' },
  selectedModel: { type: String, default: '' },
  selectedAgentLabel: { type: String, default: '' },
  selectedModelLabel: { type: String, default: '' },
  currentModelSupportsThinking: { type: Boolean, default: false },
  thinkingEffort: { type: String, default: '' },
  thinkingEffortLabel: { type: String, default: '' },
  thinkingEffortVariants: { type: Array, default: () => [] },
  groupedModels: { type: Object, default: () => ({}) },
})

const emit = defineEmits([
  'update:inputText',
  'send',
  'abort',
  'select-agent',
  'select-model',
  'select-thinking-effort',
])

const textareaRef = ref(null)
const agentOpen = ref(false)
const modelOpen = ref(false)
const thinkingOpen = ref(false)

function handleInput() {
  const el = textareaRef.value
  if (!el) return
  emit('update:inputText', el.textContent || '')
  el.style.height = 'auto'
  el.offsetHeight
  el.style.height = el.scrollHeight + 'px'
}

function handlePaste(e) {
  e.preventDefault()
  const text = (e.clipboardData || window.clipboardData).getData('text/plain')
  document.execCommand('insertText', false, text)
}

function clear() {
  if (textareaRef.value) {
    textareaRef.value.innerHTML = ''
    textareaRef.value.style.height = 'auto'
  }
}

defineExpose({ textareaRef, clear })
</script>

<style scoped>
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
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
</style>
