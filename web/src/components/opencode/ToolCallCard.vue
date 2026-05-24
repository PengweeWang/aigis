<template>
  <div class="tool-call-card" :class="msg.status">
    <div class="tool-call-header">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
      </svg>
      <span v-if="msg.subSessionId && resolvedAgent" class="tool-agent-badge" :style="{ '--color': agentColor(resolvedAgent) }">{{ resolvedAgent }}</span>
      <span class="tool-call-name">{{ msg.toolName }}</span>
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
        {{ msg.subStatus === 'running' ? '运行中...' : msg.subStatus === 'completed' ? '已完成' : msg.subStatus === 'cancelled' ? '已取消' : '已结束' }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { renderMarkdown, formatToolInput, truncateOutput, agentColor, statusLabel } from './utils.js'

const props = defineProps({
  msg: { type: Object, required: true },
})

const resolvedAgent = computed(() => {
  const m = props.msg
  return m.agent || (m.toolName === 'task' && m.input?.subagent_type) || ''
})
</script>

<style scoped>
.tool-call-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s;
  user-select: none;
}
.tool-call-card.completed { border-left: 3px solid #22c55e; }
.tool-call-card.failed { border-left: 3px solid #ef4444; }
.tool-call-card.running { border-left: 3px solid #f97316; }
.tool-call-card.cancelled { border-left: 3px solid #d1d5db; }

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 12px;
  font-size: 11px;
  color: #4b5563;
  background: #f9fafb;
  border-bottom: 1px solid #eef0f2;
  transition: background 0.15s;
}
.tool-call-card.running .tool-call-header {
  background: linear-gradient(90deg, #fff7ed, #f9fafb);
}
.tool-agent-badge {
  font-size: 10px;
  font-weight: 600;
  color: var(--color, #4f46e5);
  background: color-mix(in srgb, var(--color, #4f46e5) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--color, #4f46e5) 20%, transparent);
  border-radius: 5px;
  padding: 1px 8px;
  white-space: nowrap;
}
.tool-call-name {
  font-weight: 600;
  color: #374151;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 11px;
}
.tool-call-status {
  margin-left: auto;
  font-size: 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #9ca3af;
}
.tool-call-status.completed { color: #16a34a; }
.tool-call-status.failed { color: #dc2626; }
.tool-call-status.running { color: #ea580c; }
.tool-call-status.cancelled { color: #9ca3af; }

.sub-agent-indicator {
  font-size: 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #9ca3af;
  white-space: nowrap;
}
.sub-agent-indicator.running {
  color: #4f46e5;
}
.sub-agent-spinner {
  width: 10px;
  height: 10px;
  border: 2px solid #a5b4fc;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  display: inline-block;
  box-shadow: currentColor 0 0 4px;
}
.status-dot.running { background: #f97316; animation: pulse 1.5s infinite; }
.status-dot.completed { background: #22c55e; }
.status-dot.failed { background: #ef4444; }
.status-dot.cancelled { background: #d1d5db; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.tool-toggle {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: #9ca3af;
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.15s;
}
.tool-toggle:hover { background: #e5e7eb; color: #4b5563; }

.tool-call-body {
  padding: 10px 12px;
  background: #fafbfc;
}
.tool-section { margin-bottom: 10px; }
.tool-section:last-child { margin-bottom: 0; }
.tool-section-label {
  font-size: 10px;
  font-weight: 600;
  color: #9ca3af;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}
.tool-code {
  font-size: 10px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  user-select: text;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px 12px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  color: #4b5563;
  line-height: 1.55;
  max-height: 160px;
  overflow-y: auto;
}
.tool-code::-webkit-scrollbar {
  width: 4px;
  height: 3px;
}
.tool-code::-webkit-scrollbar-track {
  background: transparent;
}
.tool-code::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 2px;
}
.tool-code::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.22);
}
.sub-tools {
  margin-top: 10px;
  border-top: 1px solid #e5e7eb;
  padding-top: 10px;
}
.sub-tool-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-top: 6px;
  overflow: hidden;
  background: #f9fafb;
  transition: box-shadow 0.15s;
}
.sub-tool-item:hover {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.sub-tool-item.completed { border-left: 2px solid #22c55e; }
.sub-tool-item.failed { border-left: 2px solid #ef4444; }
.sub-tool-item.running { border-left: 2px solid #f97316; }
.sub-tool-header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  font-size: 10px;
  color: #4b5563;
  background: #f3f4f6;
}
.sub-tool-name {
  font-weight: 600;
  color: #374151;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 10px;
}
.sub-tool-body {
  padding: 8px 10px;
}
.sub-agent-response {
  margin-top: 8px;
}
.sub-reasoning {
  font-size: 11px;
  color: #6b7280;
  background: #f3f4f6;
  border-radius: 8px;
  padding: 10px 12px;
  line-height: 1.55;
  white-space: pre-wrap;
  border: 1px solid #e5e7eb;
}
.sub-text {
  font-size: 12px;
  line-height: 1.55;
  background: #f0f0ff;
  border: 1px solid #c7d2fe;
  border-radius: 8px;
  padding: 10px 12px;
}

.sub-agent-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  background: linear-gradient(90deg, #ede9fe, #e0e7ff);
  border-top: 1px solid #c7d2fe;
  font-size: 10px;
  color: #4c1d95;
}
.sub-agent-bar svg {
  color: #7c3aed;
}
.sub-agent-status {
  margin-left: auto;
  font-size: 10px;
  color: #9ca3af;
}
.sub-agent-status.active { color: #4f46e5; font-weight: 500; }

.md-content :deep(h1) { font-size: 17px; margin: 14px 0 8px; font-weight: 700; color: #1e1b4b; }
.md-content :deep(h2) { font-size: 15px; margin: 12px 0 6px; font-weight: 700; color: #1e1b4b; }
.md-content :deep(h3) { font-size: 13px; margin: 10px 0 4px; font-weight: 600; color: #2e1065; }
.md-content :deep(code) {
  font-size: 11px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
  background: rgba(79, 70, 229, 0.08);
  padding: 1px 5px;
  border-radius: 4px;
  color: #7c3aed;
  border: 1px solid rgba(79, 70, 229, 0.1);
}
.md-content :deep(pre) {
  background: #1e1b4b;
  border-radius: 8px;
  padding: 12px 14px;
  overflow-x: auto;
  margin: 10px 0;
}
.md-content :deep(pre)::-webkit-scrollbar {
  height: 4px;
}
.md-content :deep(pre)::-webkit-scrollbar-track {
  background: transparent;
}
.md-content :deep(pre)::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}
.md-content :deep(pre)::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.28);
}
.md-content :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 11px;
  line-height: 1.5;
  color: #e2e8f0;
  border: none;
}
.md-content :deep(strong) { font-weight: 600; color: #1e1b4b; }
</style>
