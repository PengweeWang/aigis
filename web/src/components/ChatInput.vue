<template>
  <div class="chat-input-area">
    <div class="input-toolbar">
      <ModelSelect
        :models="models"
        :selected-model="selectedModel"
        :loading="loadingModels"
        @update:selected-model="$emit('update:selectedModel', $event)"
      />
      <div class="toolbar-actions">
        <PointBadge
          :add-mode="pointAddMode"
          :count="pointCount"
          @toggle="$emit('togglePointMode')"
        />
      </div>
    </div>
    <div class="input-row">
      <n-input
        v-model:value="text"
        type="textarea"
        :placeholder="placeholder"
        :autosize="{ minRows: 1, maxRows: 4 }"
        @keydown="handleKeydown"
        :disabled="disabled"
      />
      <n-button
        type="primary"
        :disabled="!text.trim() || disabled"
        @click="send"
        class="send-btn"
        size="small"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 19V5M5 12l7-7 7 7"/>
        </svg>
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { NInput, NButton } from 'naive-ui'
import ModelSelect from './ModelSelect.vue'
import PointBadge from './PointBadge.vue'

const props = defineProps({
  models: { type: Array, default: () => [] },
  selectedModel: { type: String, default: '' },
  loadingModels: { type: Boolean, default: false },
  pointAddMode: { type: Boolean, default: false },
  pointCount: { type: Number, default: 0 },
  placeholder: { type: String, default: '请输入您的问题...' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['send', 'update:selectedModel', 'togglePointMode'])

const text = ref('')

function send() {
  const trimmed = text.value.trim()
  if (!trimmed) return
  emit('send', trimmed)
  text.value = ''
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}
</script>

<style scoped>
.chat-input-area {
  padding: 8px 12px 12px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 8px;
}

.input-toolbar > :first-child {
  flex: 1;
  max-width: 75%;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.input-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.input-row > :first-child {
  flex: 1;
}

.send-btn {
  flex-shrink: 0;
  width: 36px !important;
  height: 36px !important;
  border-radius: 10px !important;
}
</style>
