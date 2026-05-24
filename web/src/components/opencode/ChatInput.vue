<template>
  <div class="chat-input-area">
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
      <div class="input-toolbar">
        <div class="toolbar-left">
          <slot name="toolbar"></slot>
        </div>
        <div class="toolbar-right">
          <slot name="toolbar-right"></slot>
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
        <div v-if="agentOpen" class="selector-dropdown agent-dropdown">
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
        <div v-if="thinkingOpen" class="selector-dropdown thinking-dropdown">
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
  padding: 10px 16px 12px;
  border-top: 1px solid #eef0f2;
  background: #fff;
  flex-shrink: 0;
  user-select: none;
}
.editor-wrapper {
  position: relative;
  width: 100%;
  border: 1.5px solid #e5e7eb;
  border-radius: 14px;
  background: #f9fafb;
  transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
  overflow: hidden;
}
.editor-wrapper:focus-within {
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.08), 0 1px 4px rgba(0, 0, 0, 0.04);
  background: #fff;
}
.chat-textarea {
  width: 100%;
  border: none;
  border-radius: 0;
  user-select: text;
  padding: 10px 16px 4px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  min-height: 36px;
  line-height: 1.5;
  background: transparent;
  white-space: pre-wrap;
  overflow: hidden;
  word-break: break-word;
  box-sizing: border-box;
}
.chat-textarea.disabled {
  color: #9ca3af;
  pointer-events: none;
}
.chat-textarea:empty:before {
  content: attr(data-placeholder);
  color: #bbb;
  pointer-events: none;
}
.placeholder-text {
  position: absolute;
  top: 10px;
  left: 16px;
  right: 16px;
  font-size: 13px;
  color: #bbb;
  pointer-events: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 6px;
  gap: 8px;
  min-height: 34px;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
}
.toolbar-left::-webkit-scrollbar {
  height: 3px;
}
.toolbar-left::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
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
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.send-btn {
  background: linear-gradient(135deg, #4f46e5, #6366f1);
  color: #fff;
  box-shadow: 0 1px 4px rgba(79, 70, 229, 0.3);
}
.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #6366f1, #818cf8);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.4);
  transform: translateY(-1px);
}
.send-btn:active:not(:disabled) {
  transform: translateY(0) scale(0.95);
}
.send-btn:disabled {
  background: #d1d5db;
  color: #9ca3af;
  cursor: not-allowed;
  box-shadow: none;
}
.stop-btn {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
  box-shadow: 0 1px 4px rgba(239, 68, 68, 0.3);
  animation: stopPulse 2s infinite;
}
@keyframes stopPulse {
  0%, 100% { box-shadow: 0 1px 4px rgba(239, 68, 68, 0.3); }
  50% { box-shadow: 0 1px 8px rgba(239, 68, 68, 0.5); }
}
.stop-btn:hover {
  background: linear-gradient(135deg, #f87171, #ef4444);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
}

.chat-selector-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-top: 8px;
  min-height: 28px;
}
.selector-trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  cursor: pointer;
  outline: none;
  max-width: 160px;
  transition: background 0.15s, box-shadow 0.15s;
}
.selector-trigger.model-selector {
  max-width: 240px;
}
.selector-trigger.thinking-selector {
  max-width: 120px;
}
.selector-trigger:hover {
  background: rgba(79, 70, 229, 0.04);
}
.selector-trigger:focus-visible {
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
}
.selector-label {
  color: #6b7280;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.3;
}
.selector-chevron {
  flex-shrink: 0;
  color: #9ca3af;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.selector-chevron.open {
  transform: rotate(180deg);
  color: #4f46e5;
}
.selector-trigger.thinking-selector .selector-label {
  color: #7c3aed;
}
.selector-trigger.thinking-selector svg:first-child {
  color: #a5b4fc;
}
.selector-dropdown {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 0;
  min-width: 190px;
  max-height: 220px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1), 0 2px 8px rgba(0, 0, 0, 0.06);
  z-index: 100;
  padding: 6px;
  animation: dropdownIn 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}
.agent-dropdown {
  min-width: max-content;
}
.thinking-dropdown {
  min-width: 55px;
}
.selector-dropdown::-webkit-scrollbar {
  width: 4px;
}
.selector-dropdown::-webkit-scrollbar-track {
  background: transparent;
}
.selector-dropdown::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 2px;
}
.selector-dropdown::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.22);
}
@keyframes dropdownIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
.selector-group-header {
  padding: 8px 10px 4px;
  font-size: 10px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}
.selector-group-header:not(:first-child) {
  margin-top: 4px;
  border-top: 1px solid #f3f4f6;
  padding-top: 10px;
}
.selector-option {
  padding: 7px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: #4b5563;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}
.selector-option:hover {
  background: #f0f0ff;
  color: #4f46e5;
}
.selector-option.selected {
  font-weight: 600;
  color: #4f46e5;
  background: rgba(79, 70, 229, 0.06);
}
</style>
