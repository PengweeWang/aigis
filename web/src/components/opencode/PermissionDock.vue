<template>
  <div class="permission-dock">
    <div class="question-dock-header">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
      <span>权限请求</span>
    </div>
    <div class="permission-dock-body">
      <div class="question-dock-text">{{ permissionLabel(permission.permission) }}</div>
      <div v-if="permission.patterns?.length" class="permission-patterns">
        <code v-for="(pat, i) in permission.patterns" :key="i" class="permission-pattern">{{ pat }}</code>
      </div>
    </div>
    <div class="question-dock-actions">
      <button class="q-btn q-btn-cancel" :disabled="responding" @click="$emit('respond', 'reject')">拒绝</button>
      <button class="q-btn q-btn-always" :disabled="responding" @click="$emit('respond', 'always')">始终允许</button>
      <button class="q-btn q-btn-submit" :disabled="responding" @click="$emit('respond', 'once')">允许一次</button>
    </div>
  </div>
</template>

<script setup>
import { permissionLabel } from './utils.js'

defineProps({
  permission: { type: Object, required: true },
  responding: { type: Boolean, default: false },
})

defineEmits(['respond'])
</script>

<style scoped>
.permission-dock {
  padding: 14px 16px;
  border-top: 1px solid #fecaca;
  background: linear-gradient(180deg, #fff7ed 0%, #fff1f2 100%);
  flex-shrink: 0;
  user-select: none;
}
.permission-dock-body {
  margin-bottom: 10px;
}
.permission-patterns {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 6px;
}
.permission-pattern {
  font-size: 11px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  background: rgba(239, 68, 68, 0.06);
  border: 1px solid rgba(239, 68, 68, 0.1);
  padding: 4px 10px;
  border-radius: 6px;
  color: #b91c1c;
  word-break: break-all;
}

.question-dock-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #b45309;
  margin-bottom: 8px;
}
.question-dock-header svg {
  color: #f97316;
  flex-shrink: 0;
}
.question-dock-text {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
  line-height: 1.55;
}
.question-dock-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.q-btn {
  padding: 7px 16px;
  border-radius: 8px;
  border: none;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}
.q-btn:focus-visible {
  box-shadow: 0 0 0 2px rgba(180, 83, 9, 0.3);
}
.q-btn-cancel {
  background: #f3f4f6;
  color: #6b7280;
}
.q-btn-cancel:hover {
  background: #e5e7eb;
  color: #374151;
}
.q-btn-cancel:active {
  transform: scale(0.97);
}
.q-btn-always {
  background: #f3f4f6;
  color: #4b5563;
}
.q-btn-always:hover {
  background: #e5e7eb;
  color: #374151;
  border-color: #fcd34d;
}
.q-btn-always:active {
  transform: scale(0.97);
}
.q-btn-submit {
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: #fff;
  box-shadow: 0 1px 3px rgba(249, 115, 22, 0.3);
}
.q-btn-submit:hover {
  background: linear-gradient(135deg, #fb923c, #f97316);
  box-shadow: 0 2px 6px rgba(249, 115, 22, 0.4);
}
.q-btn-submit:active {
  transform: scale(0.97);
}
.q-btn-submit:disabled {
  background: #d1d5db;
  color: #9ca3af;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
