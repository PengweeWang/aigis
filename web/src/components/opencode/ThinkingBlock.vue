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
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s;
}
.thinking-block:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.thinking-block[open] {
  box-shadow: 0 1px 4px rgba(79, 70, 229, 0.08);
}
.thinking-block summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  font-size: 12px;
  font-weight: 600;
  color: #4b5563;
  cursor: pointer;
  user-select: none;
  background: #f9fafb;
  transition: background 0.15s, color 0.15s;
  outline: none;
  user-select: none;
}
.thinking-block summary::-webkit-details-marker { display: none; }
.thinking-block summary:focus-visible {
  box-shadow: inset 0 0 0 2px rgba(79, 70, 229, 0.3);
}
.thinking-block summary:hover {
  background: #f3f4f6;
  color: #4f46e5;
}
.thinking-block summary svg:first-child {
  color: #a5b4fc;
  flex-shrink: 0;
}
.thinking-block[open] summary svg:first-child {
  color: #4f46e5;
}
.thinking-block summary .chevron {
  margin-left: auto;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  color: #9ca3af;
  flex-shrink: 0;
}
.thinking-block[open] summary .chevron {
  transform: rotate(180deg);
  color: #4f46e5;
}
.thinking-block[open] summary {
  border-bottom: 1px solid #e5e7eb;
  color: #4f46e5;
}
.thinking-content {
  padding: 0 14px 14px;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.45;
  user-select: text;
}
.thinking-content :deep(p) { font-size: 12px; margin: 6px 0 0; }

.md-content :deep(h1) { font-size: 17px; margin: 14px 0 8px; font-weight: 700; color: #1e1b4b; }
.md-content :deep(h2) { font-size: 15px; margin: 12px 0 6px; font-weight: 700; color: #1e1b4b; }
.md-content :deep(h3) { font-size: 13px; margin: 10px 0 4px; font-weight: 600; color: #2e1065; }
.md-content :deep(h4) { font-size: 12px; margin: 8px 0 4px; font-weight: 600; color: #374151; }
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
.md-content :deep(ul), .md-content :deep(ol) {
  padding-left: 18px;
  margin: 4px 0;
}
.md-content :deep(li) { margin: 0; }
.md-content :deep(li::marker) { color: #a5b4fc; }
.md-content :deep(a) { color: #4f46e5; text-decoration: none; }
.md-content :deep(strong) { font-weight: 600; color: #1e1b4b; }
.md-content :deep(del) { text-decoration: line-through; color: #9ca3af; }
</style>
