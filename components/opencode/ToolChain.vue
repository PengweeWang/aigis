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

.thought-chain {
  padding: 10px 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.chain-step {
  display: flex;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #f8f9fa;
  font-size: 12px;
  transition: background 0.15s;
}
.chain-step:hover {
  background: #f0f2f5;
}
.chain-step-indicator {
  flex-shrink: 0;
  width: 20px;
  display: flex;
  justify-content: center;
  padding-top: 2px;
}
.step-icon {
  width: 16px; height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
}
.step-icon.completed { background: #52c41a; color: #fff; }
.step-icon.error { background: #ff4d4f; color: #fff; }
.step-icon.active {
  background: #1890ff;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.2);
  animation: pulse 1.5s infinite;
}
.step-icon.pending {
  background: #d9d9d9;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.chain-step-body { flex: 1; }
.chain-step-title { font-weight: 600; color: #333; }
.chain-step-content { color: #888; font-size: 11px; margin-top: 3px; }
</style>
