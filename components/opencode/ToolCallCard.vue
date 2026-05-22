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

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

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

.md-content :deep(h1) { font-size: 18px; margin: 14px 0 8px; font-weight: 700; color: #1a1a2e; }
.md-content :deep(h2) { font-size: 16px; margin: 12px 0 6px; font-weight: 700; color: #1a1a2e; }
.md-content :deep(h3) { font-size: 14px; margin: 10px 0 4px; font-weight: 600; color: #1a1a2e; }
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
.md-content :deep(strong) { font-weight: 600; color: #1a1a2e; }
</style>
