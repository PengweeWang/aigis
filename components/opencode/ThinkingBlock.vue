<template>
  <details class="thinking-block" :open="msg.expanded" @toggle="msg.expanded = $event.target.open">
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
</template>

<script setup>
import { renderMarkdown } from './utils.js'

defineProps({
  msg: { type: Object, required: true },
})
</script>

<style scoped>
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
.md-content :deep(strong) { font-weight: 600; color: #1a1a2e; }
.md-content :deep(del) { text-decoration: line-through; color: #999; }
</style>
