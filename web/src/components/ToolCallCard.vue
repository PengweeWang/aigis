<template>
  <div v-if="visible" class="tool-call-card">
    <div class="tool-call-header" @click="expanded = !expanded">
      <div class="tool-call-icon">{{ iconText }}</div>
      <div class="tool-call-title">{{ title }}</div>
      <n-tag :type="statusTagType" size="small" :bordered="false">
        {{ statusText }}
      </n-tag>
      <div class="tool-call-chevron" :class="{ expanded }">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 9l6 6 6-6"/>
        </svg>
      </div>
    </div>
    <div v-if="expanded" class="tool-call-body">
      <div class="tool-section">
        <div class="tool-section-label">输入</div>
        <div class="tool-section-content" v-html="inputHtml"></div>
      </div>
      <div v-if="outputHtml" class="tool-section">
        <div class="tool-section-label">输出</div>
        <div class="tool-section-content markdown-body" v-html="outputHtml"></div>
      </div>
      <div v-if="elapsed" class="tool-section-footer">
        耗时 {{ elapsed }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { NTag } from 'naive-ui'

const props = defineProps({
  /** @type {import('../lib/contracts').Part} */
  toolCall: { type: Object, required: true },
  inputHtml: { type: String, default: '' },
  outputHtml: { type: String, default: '' },
})

const expanded = ref(false)
const statusRef = ref(props.toolCall.state?.status || 'pending')

// Track status transitions
watch(() => props.toolCall.state?.status, (newStatus) => {
  statusRef.value = newStatus || 'pending'
  if (newStatus === 'error') expanded.value = true
})

const isRunning = computed(() => {
  const s = statusRef.value
  return s === 'pending' || s === 'running'
})

const visible = computed(() => {
  const tool = props.toolCall.tool
  if (tool === 'gis_set_final' || tool === 'todowrite' || tool === 'skill') return false
  return true
})

const iconText = computed(() => {
  const subtype = props.toolCall.state?.input?.subagent_type || props.toolCall.tool
  if (subtype === 'geocoder' || subtype === 'gis_geocode' || subtype === 'gis_reverse_geocode') return '📍'
  if (subtype === 'distance-measure' || subtype === 'gis_distance') return '📏'
  if (subtype === 'route-planner' || subtype === 'gis_route_planning') return '🗺️'
  return '🔧'
})

const title = computed(() => {
  return props.toolCall.state?.title || props.toolCall.tool || '工具调用'
})

const statusText = computed(() => {
  const s = statusRef.value
  if (s === 'pending') return '等待'
  if (s === 'running') return '执行中'
  if (s === 'error') return '失败'
  return '完成'
})

const statusTagType = computed(() => {
  const s = statusRef.value
  if (s === 'running') return 'info'
  if (s === 'pending') return 'default'
  if (s === 'error') return 'error'
  return 'success'
})

const elapsed = computed(() => {
  const t = props.toolCall.state?.time
  if (t?.start && t?.end) {
    const ms = t.end - t.start
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }
  return ''
})

</script>

<style scoped>
.tool-call-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin: 6px 0;
  overflow: hidden;
  background: #fafafa;
  transition: border-color 0.2s;
}

.tool-call-card:hover {
  border-color: #d0d0d0;
}

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  font-size: 12px;
}

.tool-call-header:hover {
  background: #f5f5f5;
}

.tool-call-icon {
  font-size: 14px;
}

.tool-call-title {
  flex: 1;
  font-weight: 500;
  color: #444;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-call-chevron {
  color: #999;
  transition: transform 0.2s;
}

.tool-call-chevron.expanded {
  transform: rotate(180deg);
}

.tool-call-body {
  padding: 0 12px 12px;
  border-top: 1px solid #f0f0f0;
}

.tool-section {
  margin-top: 10px;
}

.tool-section-label {
  font-size: 11px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.tool-section-content {
  font-size: 12px;
  color: #555;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.tool-section-content.markdown-body :deep(p) {
  margin: 4px 0;
}

.tool-section-content.markdown-body :deep(code) {
  background: #f0f0f0;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 11px;
}

.tool-section-content.markdown-body :deep(pre) {
  background: #f5f5f5;
  padding: 8px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 11px;
}

.tool-section-content.markdown-body :deep(table) {
  font-size: 11px;
  border-collapse: collapse;
}

.tool-section-content.markdown-body :deep(th),
.tool-section-content.markdown-body :deep(td) {
  border: 1px solid #e0e0e0;
  padding: 4px 8px;
}

.tool-section-footer {
  margin-top: 8px;
  font-size: 11px;
  color: #aaa;
}

@keyframes statusPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

:deep(.n-tag.n-tag--info) {
  animation: statusPulse 1.5s infinite ease-in-out;
}
</style>
