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
  padding: 12px 14px;
  border-top: 1px solid #e8e8e8;
  background: linear-gradient(135deg, #fff5f5, #fff0f0);
}
.permission-dock-body {
  margin-bottom: 8px;
}
.permission-patterns {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.permission-pattern {
  font-size: 11px;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  background: rgba(0,0,0,0.05);
  padding: 3px 8px;
  border-radius: 4px;
  color: #cf1322;
  word-break: break-all;
}

.question-dock-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #d48806;
  margin-bottom: 8px;
}
.question-dock-text {
  font-size: 11px;
  color: #666;
  margin-bottom: 8px;
  line-height: 1.5;
}
.question-dock-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}
.q-btn {
  padding: 6px 14px;
  border-radius: 6px;
  border: none;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.q-btn-cancel { background: #f0f0f0; color: #666; }
.q-btn-cancel:hover { background: #e4e4e4; }
.q-btn-always {
  background: #f0f0f0;
  color: #555;
}
.q-btn-always:hover {
  background: #e4e4e4;
}
.q-btn-submit { background: #d48806; color: #fff; }
.q-btn-submit:hover { background: #e8a020; }
.q-btn-submit:disabled { background: #d9d9d9; color: #fff; cursor: not-allowed; }
</style>
