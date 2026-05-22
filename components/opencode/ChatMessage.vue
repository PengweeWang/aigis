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
        <div class="md-content" v-html="renderMarkdown(msg.content)"></div>
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
  animation: msgFadeIn 0.2s ease;
}
@keyframes msgFadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
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
  line-height: 1.55;
  word-break: break-word;
}
.bubble.assistant {
  background: #fff;
  color: #1a1a2e;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.bubble.user {
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.25);
}
.bubble.user .points-card {
  --text-color: #1a5cc8;
  --bg-color: #f0f5ff;
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
  gap: 4px;
  padding: 4px 0;
}
.loading-indicator .dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #bbb;
  animation: dotBounce 1.4s infinite ease-in-out;
}
.loading-indicator .dot:nth-child(1) { animation-delay: 0s; }
.loading-indicator .dot:nth-child(2) { animation-delay: 0.16s; }
.loading-indicator .dot:nth-child(3) { animation-delay: 0.32s; }
@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.md-content {
  font-size: 13px;
  line-height: 1.6;
}
.md-content :deep(p) { margin: 0 0 8px; }
.md-content :deep(p:last-child) { margin-bottom: 0; }
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
.md-content :deep(a:hover) { text-decoration: underline; }
.md-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 12px;
  border-radius: 8px;
  overflow: hidden;
}
.md-content :deep(th), .md-content :deep(td) {
  border: 1px solid #e8e8e8;
  padding: 8px 12px;
  text-align: left;
}
.md-content :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
  color: #333;
}
.md-content :deep(tbody tr:nth-child(even)) {
  background: #fafbfc;
}
.md-content :deep(hr) {
  border: none;
  border-top: 1px solid #e8e8e8;
  margin: 14px 0;
}
.md-content :deep(blockquote) {
  margin: 8px 0;
  padding: 6px 14px;
  border-left: 3px solid #d0d5dd;
  color: #666;
  font-size: 12px;
  background: #f8f9fa;
  border-radius: 0 6px 6px 0;
}
.md-content :deep(strong) { font-weight: 600; color: #1a1a2e; }
.md-content :deep(del) { text-decoration: line-through; color: #999; }
.md-content :deep(br) { content: ''; display: block; margin: 4px 0; }

.md-content[data-typing]::after {
  content: '|';
  display: inline;
  animation: cursorBlink 0.8s step-end infinite;
  color: #1890ff;
  font-weight: 500;
}
@keyframes cursorBlink {
  50% { opacity: 0; }
}

.user-text {
  font-size: 13px;
  line-height: 1.5;
}

.system-msg {
  width: 100%;
  text-align: center;
  font-size: 11px;
  color: #999;
  padding: 4px 0;
}

.points-card {
  background: linear-gradient(135deg, #f0f5ff, #e8f0fe);
  border: 1px solid #d6e4ff;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 8px;
}
.points-card-header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  background: rgba(24, 144, 255, 0.08);
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
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: 9px;
  padding: 0 5px;
}
.points-card-body { padding: 6px 10px; }
.point-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  font-size: 11px;
}
.point-item + .point-item { border-top: 1px solid #e6f0ff; }
.point-label {
  width: 22px; height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(24, 144, 255, 0.3);
}
.point-coords {
  color: #666;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 10px;
}
</style>
