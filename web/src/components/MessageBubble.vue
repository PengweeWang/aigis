<template>
  <div
    class="message-bubble"
    :class="[`message-${msg.role}`]"
  >
    <!-- Reasoning message (standalone) -->
    <ReasoningPanel
      v-if="msg.type === 'reasoning'"
      :content="msg.content"
      :expanded="msg.expanded || false"
    />

    <!-- System message -->
    <div v-else-if="msg.type === 'system'" class="system-text">
      <span class="system-dot"></span>
      {{ msg.content }}
    </div>

    <!-- User message with point card -->
    <template v-else-if="msg.role === 'user'">
      <div v-if="msg.points?.length" class="points-card">
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
      <div class="user-text">{{ msg.userText || msg.content }}</div>
    </template>

    <!-- Assistant message with markdown -->
    <div v-else-if="msg.role === 'assistant'" class="assistant-content">
      <!-- Tool call cards -->
      <ToolCallCard
        v-for="tc in visibleToolCalls"
        :key="tc.id"
        :tool-call="tc"
        :input-html="getInputHtml(tc)"
        :output-html="getOutputHtml(tc)"
      />
      <!-- Markdown content -->
      <div
        v-if="msg.content || msg.typing"
        class="markdown-body"
        v-html="contentHtml"
      ></div>
      <!-- Loading skeleton -->
      <div v-if="msg.loading" class="loading-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import DOMPurify from 'dompurify'
import { renderMarkdown, renderMarkdownSync } from '../lib/markdown'
import ReasoningPanel from './ReasoningPanel.vue'
import ToolCallCard from './ToolCallCard.vue'

const props = defineProps({
  /** @type {import('../lib/contracts').Message} */
  msg: { type: Object, required: true },
})

const contentHtml = ref('')

const visibleToolCalls = computed(() => {
  if (!props.msg.toolCalls) return []
  return props.msg.toolCalls.filter(tc => {
    // Only show task dispatches (user-facing sub-agent calls)
    if (tc.tool === 'task') return true
    // Show MCP tool calls that have meaningful output
    if (tc.tool === 'gis_geocode' || tc.tool === 'gis_reverse_geocode') return true
    if (tc.tool === 'gis_route_planning' || tc.tool === 'gis_distance') return true
    return false
  })
})

function getInputHtml(tc) {
  if (!tc?.state?.input) return ''
  try {
    const text = typeof tc.state.input === 'string'
      ? tc.state.input
      : JSON.stringify(tc.state.input, null, 2)
    return DOMPurify.sanitize(renderMarkdownSync('```json\n' + text + '\n```'))
  } catch {
    return ''
  }
}

function getOutputHtml(tc) {
  if (!tc?.state?.output) return ''
  // No cache — tool output can change (running → completed)
  return DOMPurify.sanitize(renderMarkdownSync(tc.state.output))
}

// Render markdown content reactively
watch(() => props.msg.content, async (val) => {
  if (!val && !props.msg.typing) {
    contentHtml.value = ''
    return
  }
  const text = val || ''
  if (props.msg.typing) {
    // During streaming, render sync to keep up with deltas
    try {
      contentHtml.value = DOMPurify.sanitize(renderMarkdownSync(text))
    } catch {
      contentHtml.value = ''
    }
    // Append blink cursor
    if (text.length > 0) {
      contentHtml.value += '<span class="cursor-blink">|</span>'
    }
  } else {
    // Final render with Shiki
    try {
      const raw = await renderMarkdown(text)
      contentHtml.value = DOMPurify.sanitize(raw)
    } catch {
      contentHtml.value = DOMPurify.sanitize(renderMarkdownSync(text))
    }
  }
}, { immediate: true })

onMounted(async () => {
  if (props.msg.content && !props.msg.typing) {
    try {
      const raw = await renderMarkdown(props.msg.content)
      contentHtml.value = DOMPurify.sanitize(raw)
    } catch {
      contentHtml.value = DOMPurify.sanitize(renderMarkdownSync(props.msg.content))
    }
  }
})
</script>

<style scoped>
.message-bubble {
  margin-bottom: 12px;
  font-size: 13px;
}

/* System message */
.system-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 11px;
  color: #999;
  padding: 4px 0;
}

.system-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #d0d0d0;
}

/* User message */
.message-user {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.user-text {
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  padding: 8px 14px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.5;
  max-width: 85%;
  word-break: break-word;
}

/* Points card */
.points-card {
  background: #f0f5ff;
  border: 1px solid #d6e4ff;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 8px;
  width: 100%;
  max-width: 85%;
}

.points-card-header {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #e6f0ff;
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
  min-width: 16px;
  height: 16px;
  line-height: 16px;
  text-align: center;
  border-radius: 8px;
  padding: 0 4px;
}

.points-card-body {
  padding: 4px 8px;
}

.point-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 0;
  font-size: 11px;
}

.point-item + .point-item {
  border-top: 1px solid #e6f0ff;
}

.point-label {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #1890ff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}

.point-coords {
  color: #666;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 10px;
}

/* Assistant message */
.message-assistant {
  display: flex;
  flex-direction: column;
}

.assistant-content {
  max-width: 100%;
}

/* Markdown */
.markdown-body {
  font-size: 13px;
  line-height: 1.7;
  color: #333;
  word-break: break-word;
}

.markdown-body :deep(h1) { font-size: 16px; margin: 12px 0 6px; }
.markdown-body :deep(h2) { font-size: 14px; margin: 10px 0 4px; }
.markdown-body :deep(h3) { font-size: 13px; margin: 8px 0 4px; }
.markdown-body :deep(p) { margin: 4px 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 16px; }
.markdown-body :deep(li) { margin: 2px 0; }
.markdown-body :deep(code) {
  background: #f0f0f0;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 11px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
}
.markdown-body :deep(pre) {
  background: #f8f8f8;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px;
  overflow-x: auto;
  margin: 8px 0;
}
.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 12px;
}
.markdown-body :deep(blockquote) {
  border-left: 3px solid #1890ff;
  padding-left: 12px;
  color: #888;
  margin: 6px 0;
}
.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 12px;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
  border: 1px solid #e0e0e0;
  padding: 6px 10px;
  text-align: left;
}
.markdown-body :deep(th) {
  background: #f5f5f5;
  font-weight: 600;
}
.markdown-body :deep(a) {
  color: #1890ff;
  text-decoration: none;
}
.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

/* Loading dots */
.loading-dots {
  display: flex;
  gap: 6px;
  padding: 8px 0;
}

.loading-dots span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #d0d0d0;
  animation: dotPulse 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }
.loading-dots span:nth-child(3) { animation-delay: 0s; }

@keyframes dotPulse {
  0%, 80%, 100% { transform: scale(0.8); background: #d0d0d0; }
  40% { transform: scale(1); background: #1890ff; }
}
</style>
