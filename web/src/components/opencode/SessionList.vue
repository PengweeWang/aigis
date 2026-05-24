<template>
  <div class="session-list">
    <div class="session-list-header">
      <span class="session-list-title">历史会话</span>
      <button class="icon-btn close-btn" @click="$emit('close')" title="关闭">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
    <div class="session-list-body" v-if="!loading">
      <div v-if="sessions.length === 0" class="session-empty">暂无历史会话</div>
      <div
        v-for="s in sessions"
        :key="s.id"
        class="session-item"
        :class="{ active: s.id === currentSessionId }"
        @click="$emit('switch', s.id)"
      >
        <div class="session-item-title">{{ s.title || '未命名会话' }}</div>
        <div class="session-item-meta">
          <span class="session-item-id">{{ s.id.slice(0, 8) }}</span>
          <span v-if="s.time?.created" class="session-item-time">{{ formatTime(s.time.created) }}</span>
        </div>
        <button
          class="session-item-delete"
          title="删除会话"
          @click.stop="$emit('delete', s.id)"
        >
          <svg width="12" height="12" viewBox="0 0 14 14" fill="none">
            <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </div>
    <div v-else class="session-loading">加载中...</div>
  </div>
</template>

<script setup>
defineProps({
  sessions: { type: Array, default: () => [] },
  currentSessionId: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})

defineEmits(['close', 'switch', 'delete'])

function formatTime(ts) {
  if (!ts) return ''
  try {
    const d = new Date(typeof ts === 'number' ? ts : ts)
    if (isNaN(d.getTime())) return ''
    const now = new Date()
    const diffMs = now - d
    const diffMin = Math.floor(diffMs / 60000)
    if (diffMin < 1) return '刚刚'
    if (diffMin < 60) return `${diffMin}分钟前`
    const diffHour = Math.floor(diffMin / 60)
    if (diffHour < 24) return `${diffHour}小时前`
    const diffDay = Math.floor(diffHour / 24)
    if (diffDay < 7) return `${diffDay}天前`
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch {
    return ''
  }
}
</script>

<style scoped>
.session-list {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 30;
  background: var(--panel-bg, #fff);
  display: flex;
  flex-direction: column;
}
.session-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--header-border, #eef0f2);
  background: linear-gradient(180deg, var(--header-bg-from, #fafbfc) 0%, var(--header-bg-to, #f7f8fa) 100%);
  flex-shrink: 0;
}
.session-list-title {
  font-size: 14px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--header-title-from, #1e1b4b), var(--header-title-to, #312e81));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.close-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--icon-btn-bg, #f1f3f5);
  color: var(--icon-btn-color, #555);
  transition: all 0.15s;
}
.close-btn:hover {
  background: var(--icon-btn-hover-bg, #e5e8eb);
  color: #333;
}
.session-list-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.session-list-body::-webkit-scrollbar {
  width: 4px;
}
.session-list-body::-webkit-scrollbar-track {
  background: transparent;
}
.session-list-body::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 2px;
}
.session-list-body::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.22);
}
.session-empty {
  text-align: center;
  color: #999;
  font-size: 13px;
  padding: 40px 0;
}
.session-loading {
  text-align: center;
  color: #999;
  font-size: 13px;
  padding: 40px 0;
}
.session-item {
  position: relative;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 2px;
}
.session-item:hover {
  background: var(--icon-btn-bg, #f1f3f5);
}
.session-item.active {
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.15);
}
.session-item-title {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a2e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 20px;
}
.session-item-meta {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  font-size: 11px;
  color: #999;
}
.session-item-id {
  font-family: monospace;
}
.session-item-delete {
  position: absolute;
  top: 10px;
  right: 8px;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  display: none;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #999;
  transition: all 0.15s;
}
.session-item:hover .session-item-delete {
  display: inline-flex;
}
.session-item-delete:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}
</style>
