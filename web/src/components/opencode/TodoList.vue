<template>
  <div v-if="visible" class="todo-list" :class="{ 'all-done': allDone, 'fade-out': fadingOut }">
    <div class="todo-header" :class="{ 'done-header': allDone }">
      <svg v-if="!allDone" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 11l3 3L22 4"/>
        <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
      </svg>
      <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
        <path d="M22 4L12 14.01l-3-3"/>
      </svg>
      <span>{{ allDone ? '全部完成' : '任务清单' }}</span>
      <span class="todo-count">{{ doneCount }}/{{ todos.length }}</span>
    </div>
    <div class="todo-items">
      <div v-for="t in todos" :key="t.id || t.content" class="todo-item" :class="{ done: t.status === 'completed' }">
        <span class="todo-check">
          <svg v-if="t.status === 'completed'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <path d="M20 6L9 17l-5-5"/>
          </svg>
          <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="9"/>
          </svg>
        </span>
        <span class="todo-text">{{ t.content || t.text || t.title }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  todos: { type: Array, default: () => [] },
})

const visible = ref(true)
const fadingOut = ref(false)
let hideTimer = null

const doneCount = computed(() => props.todos.filter(t => t.status === 'completed').length)
const allDone = computed(() => props.todos.length > 0 && doneCount.value === props.todos.length)

watch(allDone, (v) => {
  clearTimeout(hideTimer)
  if (v) {
    hideTimer = setTimeout(() => {
      fadingOut.value = true
      setTimeout(() => { visible.value = false }, 400)
    }, 2000)
  } else {
    visible.value = true
    fadingOut.value = false
  }
})

watch(() => props.todos.length, (newLen, oldLen) => {
  if (newLen > 0 && oldLen === 0) {
    visible.value = true
    fadingOut.value = false
  }
})
</script>

<style scoped>
.todo-list {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: opacity 0.4s ease, transform 0.4s ease;
}
.todo-list.fade-out {
  opacity: 0;
  transform: translateY(-8px);
}
.todo-list.all-done {
  border-color: #bbf7d0;
}
.todo-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
  border-bottom: 1px solid #d1fae5;
  font-size: 12px;
  font-weight: 600;
  color: #166534;
  transition: background 0.3s, color 0.3s;
}
.todo-header.done-header {
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  color: #15803d;
}
.todo-count {
  margin-left: auto;
  font-size: 11px;
  font-weight: 500;
  color: #6b7280;
}
.todo-items {
  padding: 6px 0;
}
.todo-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 5px 12px;
  font-size: 12px;
  line-height: 1.5;
  color: #374151;
  transition: background 0.1s;
}
.todo-item:hover {
  background: #f9fafb;
}
.todo-item.done .todo-text {
  color: #9ca3af;
  text-decoration: line-through;
}
.todo-check {
  flex-shrink: 0;
  margin-top: 2px;
  color: #9ca3af;
}
.todo-item.done .todo-check {
  color: #22c55e;
}
.todo-text {
  flex: 1;
  word-break: break-word;
}
</style>
