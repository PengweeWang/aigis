<template>
  <div ref="listRef" class="message-list">
    <div class="messages-inner">
      <div v-if="items.length === 0 && !showWelcome" class="empty-state">
        <div class="empty-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <div class="empty-text">开始对话...</div>
      </div>
      <template v-for="msg in items" :key="msg.id">
        <MessageBubble :msg="msg" />
      </template>
    </div>
    <div ref="bottomRef"></div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import MessageBubble from './MessageBubble.vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  showWelcome: { type: Boolean, default: false },
})

const listRef = ref(null)
const bottomRef = ref(null)

const emit = defineEmits(['scroll-ready'])

function scrollToBottom() {
  nextTick(() => {
    bottomRef.value?.scrollIntoView?.({ behavior: 'smooth' })
  })
}

function scrollToBottomInstant() {
  nextTick(() => {
    bottomRef.value?.scrollIntoView?.({ behavior: 'instant' })
  })
}

// Expose for store
defineExpose({ scrollToBottom, scrollToBottomInstant })

onMounted(() => {
  emit('scroll-ready')
})

// Auto-scroll on new items
let userScrolledUp = false

watch(() => props.items.length, () => {
  if (!userScrolledUp) scrollToBottom()
})

// Detect user scroll to prevent auto-scroll during streaming
if (typeof window !== 'undefined') {
  // Attach scroll listener on the list container
  onMounted(() => {
    const el = listRef.value
    if (!el) return
    el.addEventListener('scroll', () => {
      const threshold = 60
      const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold
      userScrolledUp = !atBottom
    })
  })
}
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.messages-inner {
  display: flex;
  flex-direction: column;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 12px;
}

.empty-icon {
  opacity: 0.4;
}

.empty-text {
  font-size: 13px;
  color: #ccc;
}
</style>
