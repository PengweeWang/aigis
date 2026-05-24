<template>
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
        <div class="user-text">{{ msg.content }}</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { renderMarkdown } from './utils.js'

defineProps({
  msg: { type: Object, required: true },
})
</script>

<style scoped>
.msg-row {
  display: flex;
  animation: msgFadeIn 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
}
@keyframes msgFadeIn {
  from { opacity: 0; transform: translateY(6px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
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

.bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
}
.bubble.assistant {
  background: #fff;
  color: #1e1b4b;
  border-top-left-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
}
.bubble.user {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: #fff;
  border-top-right-radius: 4px;
  box-shadow: 0 2px 10px rgba(79, 70, 229, 0.3), 0 1px 3px rgba(0, 0, 0, 0.08);
}
.bubble.user .points-card {
  --text-color: #4c1d95;
  --bg-color: #ede9fe;
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
  gap: 5px;
  padding: 4px 0;
}
.loading-indicator .dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a5b4fc, #818cf8);
  animation: dotBounce 1.4s infinite ease-in-out;
}
.loading-indicator .dot:nth-child(1) { animation-delay: 0s; }
.loading-indicator .dot:nth-child(2) { animation-delay: 0.16s; }
.loading-indicator .dot:nth-child(3) { animation-delay: 0.32s; }
@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0.5); opacity: 0.3; }
  40% { transform: scale(1); opacity: 1; }
}

.md-content {
  font-size: 13px;
  line-height: 1.65;
  user-select: text;
}
.md-content :deep(p) { margin: 0 0 6px; }
.md-content :deep(p:last-child) { margin-bottom: 0; }
.md-content :deep(h1) { font-size: 18px; margin: 16px 0 8px; font-weight: 700; color: #1e1b4b; }
.md-content :deep(h2) { font-size: 16px; margin: 14px 0 6px; font-weight: 700; color: #1e1b4b; }
.md-content :deep(h3) { font-size: 14px; margin: 12px 0 4px; font-weight: 600; color: #2e1065; }
.md-content :deep(h4) { font-size: 13px; margin: 10px 0 4px; font-weight: 600; color: #374151; }
.md-content :deep(code) {
  font-size: 12px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
  background: rgba(79, 70, 229, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
  color: #7c3aed;
  border: 1px solid rgba(79, 70, 229, 0.12);
}
.md-content :deep(pre) {
  background: #1e1b4b;
  border-radius: 10px;
  padding: 14px 16px;
  overflow-x: auto;
  margin: 10px 0;
  border: 1px solid rgba(255, 255, 255, 0.05);
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
  font-size: 12px;
  line-height: 1.55;
  color: #e2e8f0;
  border: none;
}
.md-content :deep(ul), .md-content :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}
.md-content :deep(li) { margin: 0; }
.md-content :deep(li::marker) { color: #a5b4fc; }
.md-content :deep(a) { color: #4f46e5; text-decoration: none; font-weight: 500; }
.md-content :deep(a:hover) { text-decoration: underline; }
.md-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 12px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}
.md-content :deep(th), .md-content :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  text-align: left;
}
.md-content :deep(th) {
  background: #f3f4f6;
  font-weight: 600;
  color: #374151;
}
.md-content :deep(tbody tr:nth-child(even)) {
  background: #f9fafb;
}
.md-content :deep(hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 14px 0;
}
.md-content :deep(blockquote) {
  margin: 8px 0;
  padding: 6px 14px;
  border-left: 3px solid #c7d2fe;
  color: #6b7280;
  font-size: 12px;
  background: #f5f3ff;
  border-radius: 0 6px 6px 0;
}
.md-content :deep(strong) { font-weight: 600; color: #1e1b4b; }
.md-content :deep(del) { text-decoration: line-through; color: #9ca3af; }
.md-content :deep(br) { content: ''; display: block; margin: 4px 0; }

.md-content[data-typing]::after {
  content: '';
  display: inline-block;
  width: 2px;
  height: 15px;
  background: #4f46e5;
  margin-left: 2px;
  vertical-align: text-bottom;
  border-radius: 1px;
  animation: cursorBlink 0.9s step-end infinite;
}
@keyframes cursorBlink {
  50% { opacity: 0; }
}

.user-text {
  font-size: 13px;
  line-height: 1.55;
}

.system-msg {
  width: 100%;
  text-align: center;
  font-size: 11px;
  color: #9ca3af;
  padding: 4px 0;
  letter-spacing: 0.2px;
}

.points-card {
  background: linear-gradient(135deg, #ede9fe, #e0e7ff);
  border: 1px solid #c7d2fe;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 8px;
}
.points-card-header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 10px;
  background: rgba(79, 70, 229, 0.06);
  font-size: 11px;
  font-weight: 600;
  color: #4c1d95;
  border-bottom: 1px solid #c7d2fe;
}
.points-count {
  margin-left: auto;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: #fff;
  font-size: 9px;
  font-weight: 600;
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: 9px;
  padding: 0 5px;
  box-shadow: 0 1px 3px rgba(79, 70, 229, 0.3);
}
.points-card-body { padding: 6px 10px; }
.point-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 11px;
}
.point-item + .point-item { border-top: 1px solid #d5d0ff; }
.point-label {
  width: 22px; height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(79, 70, 229, 0.35);
}
.point-coords {
  color: #6b7280;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 10px;
}
</style>
