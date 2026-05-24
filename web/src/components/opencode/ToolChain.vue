<template>
  <details class="thinking-block" :open="msg.expanded" @toggle="msg.expanded = $event.target.open">
    <summary>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
      </svg>
      <span>工具调用链</span>
      <svg class="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M6 9l6 6 6-6"/>
      </svg>
    </summary>
    <div class="thought-chain">
      <div v-for="(step, i) in msg.steps" :key="i" class="chain-step" :class="step.status">
        <div class="chain-step-indicator">
          <span v-if="step.status === 'completed'" class="step-icon completed">&#10003;</span>
          <span v-else-if="step.status === 'error'" class="step-icon error">&#10007;</span>
          <span v-else-if="step.status === 'active'" class="step-icon active"></span>
          <span v-else class="step-icon pending"></span>
        </div>
        <div class="chain-step-body">
          <div class="chain-step-title">{{ step.title }}</div>
          <div v-if="step.content" class="chain-step-content">{{ step.content }}</div>
        </div>
      </div>
    </div>
  </details>
</template>

<script setup>
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
  user-select: none;
}
.thinking-block:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.thinking-block[open] {
  box-shadow: 0 1px 4px rgba(249, 115, 22, 0.08);
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
}
.thinking-block summary::-webkit-details-marker { display: none; }
.thinking-block summary:focus-visible {
  box-shadow: inset 0 0 0 2px rgba(249, 115, 22, 0.3);
}
.thinking-block summary:hover {
  background: #f3f4f6;
  color: #ea580c;
}
.thinking-block summary svg:first-child {
  color: #f97316;
  flex-shrink: 0;
}
.thinking-block summary .chevron {
  margin-left: auto;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  color: #9ca3af;
  flex-shrink: 0;
}
.thinking-block[open] summary .chevron {
  transform: rotate(180deg);
  color: #ea580c;
}
.thinking-block[open] summary {
  border-bottom: 1px solid #e5e7eb;
  color: #ea580c;
}

.thought-chain {
  padding: 10px 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.chain-step {
  display: flex;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 8px;
  background: #f8f9fa;
  font-size: 12px;
  transition: background 0.15s, box-shadow 0.15s;
  position: relative;
}
.chain-step:hover {
  background: #f3f4f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.chain-step-indicator {
  flex-shrink: 0;
  width: 20px;
  display: flex;
  justify-content: center;
  padding-top: 2px;
}
.chain-step-indicator::after {
  content: '';
  position: absolute;
  left: 19px;
  top: 28px;
  width: 2px;
  bottom: -8px;
  background: #e5e7eb;
  border-radius: 1px;
}
.chain-step:last-child .chain-step-indicator::after {
  display: none;
}
.step-icon {
  width: 18px; height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
  position: relative;
  z-index: 1;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}
.step-icon.completed { background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; }
.step-icon.error { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; }
.step-icon.active {
  background: linear-gradient(135deg, #f97316, #ea580c);
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.25);
  animation: pulse 1.5s infinite;
}
.step-icon.pending {
  background: #d1d5db;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.chain-step-body { flex: 1; min-width: 0; }
.chain-step-title { font-weight: 600; color: #374151; line-height: 1.4; }
.chain-step-content { color: #9ca3af; font-size: 11px; margin-top: 3px; line-height: 1.4; }
</style>
