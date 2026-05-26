<template>
  <div
    v-if="visible"
    class="floating-chat-card"
    :class="{ collapsed: isCollapsed }"
    :style="cardStyle"
  >
    <!-- Header (drag handle) -->
    <div ref="headerRef" class="card-header">
      <div class="header-left">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2">
          <path d="M4 8h16M4 16h16"/>
        </svg>
        <span class="header-title">AIGIS</span>
      </div>
      <div class="header-right">
        <n-tooltip>
          <template #trigger>
            <n-button class="header-btn" size="tiny" quaternary circle @click="handleNewSession">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 5v14M5 12h14"/>
              </svg>
            </n-button>
          </template>
          新建会话
        </n-tooltip>
        <n-tooltip>
          <template #trigger>
            <n-button class="header-btn" size="tiny" quaternary circle @click="toggleCollapse">
              <svg v-if="isCollapsed" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 15l7-7 7 7"/>
              </svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 9l7 7 7-7"/>
              </svg>
            </n-button>
          </template>
          {{ isCollapsed ? '展开' : '折叠' }}
        </n-tooltip>
      </div>
    </div>

    <!-- Body (hidden when collapsed) -->
    <div v-show="!isCollapsed" class="card-body">
      <MessageList
        ref="messageListRef"
        :items="messagesStore.items"
        @scroll-ready="onScrollReady"
      />
      <ChatInput
        :models="sessionStore.models"
        :selected-model="sessionStore.selectedModel"
        :loading-models="sessionStore.isLoadingModels"
        :point-add-mode="mapStore.addModeEnabled"
        :point-count="pointCount"
        @send="handleSend"
        @update:selected-model="sessionStore.setModel"
        @toggle-point-mode="handleTogglePointMode"
      />
    </div>

    <!-- Resize handle -->
    <div
      v-show="!isCollapsed"
      class="resize-handle"
      @mousedown="startResize"
    ></div>

    <!-- Collapsed pill -->
    <div v-if="isCollapsed" class="collapsed-pill" @click="isCollapsed = false">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject } from 'vue'
import { NButton, NTooltip } from 'naive-ui'
import { useSessionStore } from '../stores/session'
import { useMessagesStore } from '../stores/messages'
import { useMapStore } from '../stores/map'
import { useSSE } from '../composables/useSSE'
import { useMapDataSocket } from '../composables/useMapDataSocket'
import ChatInput from './ChatInput.vue'
import MessageList from './MessageList.vue'

// Map container injected from App.vue
const mapContainer = inject('mapContainer', null)

// Stores
const sessionStore = useSessionStore()
const messagesStore = useMessagesStore()
const mapStore = useMapStore()

// SSE & WS
const sse = useSSE()
const ws = useMapDataSocket(mapContainer)

const messageListRef = ref(null)
const headerRef = ref(null)

// Card state
const isCollapsed = ref(false)
const visible = ref(false)
const cardWidth = ref(420)
const pointCount = ref(0)

function syncPointCount() {
  pointCount.value = (mapContainer?.getUserPoints?.() || []).length
}

// Drag state
const dragX = ref(0)
const dragY = ref(0)
const isDragging = ref(false)
let dragStartX = 0
let dragStartY = 0
let dragOrigX = 0
let dragOrigY = 0

// Resize state
const resizing = ref(false)

const cardStyle = computed(() => ({
  width: isCollapsed.value ? '48px' : cardWidth.value + 'px',
  transform: `translate(${dragX.value}px, ${dragY.value}px)`,
  transition: isDragging.value ? 'none' : 'transform 0.2s ease',
}))

function onScrollReady() {
  messagesStore.registerScroll(() => {
    messageListRef.value?.scrollToBottom?.()
  })
  messageListRef.value?.scrollToBottom?.()
}

async function handleSend(text) {
  mapContainer?.clearMarkers?.()
  mapContainer?.clearPolylines?.()
  const points = mapContainer?.getUserPoints?.() || []

  let fullText = text
  if (points.length > 0) {
    const pointsDesc = points.map(p => `${p.label} (${p.lng}, ${p.lat})`).join('\n')
    fullText = `[地图标注点]\n${pointsDesc}\n\n[用户问题]\n${text}`
  }

  await messagesStore.sendMessage(fullText, points.length > 0 ? points : undefined, text)
  syncPointCount()
}

function handleNewSession() {
  messagesStore.clearAll()
  mapContainer?.clearMarkers?.()
  mapContainer?.clearPolylines?.()
  mapContainer?.clearUserPoints?.()
  mapStore.clearUserPoints()
  pointCount.value = 0
  sessionStore.createSession()
  messagesStore.addSystemMessage('已创建新会话')
}

function handleTogglePointMode() {
  mapStore.toggleAddMode()
  if (mapStore.addModeEnabled) {
    mapContainer?.enableAddMode?.()
  } else {
    mapContainer?.disableAddMode?.()
  }
}

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

// Drag
function onHeaderPointerDown(e) {
  if (e.target.closest('.header-btn')) return
  isDragging.value = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragOrigX = dragX.value
  dragOrigY = dragY.value
  document.addEventListener('pointermove', onPointerMove)
  document.addEventListener('pointerup', onPointerUp)
}

function onPointerMove(e) {
  const dx = e.clientX - dragStartX
  const dy = e.clientY - dragStartY
  // Clamp — card positioned top-right, so allow left/down movement mainly
  dragX.value = Math.min(0, Math.max(dragOrigX + dx, -(window.innerWidth - 480)))
  dragY.value = Math.max(0, Math.min(dragOrigY + dy, window.innerHeight - 100))
}

function onPointerUp() {
  isDragging.value = false
  document.removeEventListener('pointermove', onPointerMove)
  document.removeEventListener('pointerup', onPointerUp)
}

// Resize
function startResize(e) {
  resizing.value = true
  const startX = e.clientX
  const startW = cardWidth.value
  function onMove(ev) {
    cardWidth.value = Math.max(320, Math.min(700, startW - (ev.clientX - startX)))
  }
  function onUp() {
    resizing.value = false
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
  e.preventDefault()
}

// Init
onMounted(async () => {
  const healthy = await sessionStore.checkHealth()
  if (healthy) {
    messagesStore.addSystemMessage(`已连接至GIS智能体${sessionStore.serverVersion ? '，版本: ' + sessionStore.serverVersion : ''}`)
    await sessionStore.fetchModels()
    await sessionStore.createSession()
    visible.value = true
  } else {
    messagesStore.addSystemMessage('无法连接到OpenCode服务器，请确保已运行 opencode serve')
    visible.value = true
  }

  sse.connect()
  ws.connect()

  // Attach drag handler
  const header = headerRef.value
  if (header) {
    header.addEventListener('pointerdown', onHeaderPointerDown)
  }
})

onUnmounted(() => {
  sse.disconnect()
  ws.disconnect()
  document.removeEventListener('pointermove', onPointerMove)
  document.removeEventListener('pointerup', onPointerUp)
  const header = headerRef.value
  if (header) {
    header.removeEventListener('pointerdown', onHeaderPointerDown)
  }
})
</script>

<style scoped>
.floating-chat-card {
  position: fixed;
  top: 24px;
  right: 24px;
  bottom: 24px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12), 0 1px 3px rgba(0, 0, 0, 0.04);
  z-index: 100;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.floating-chat-card.collapsed {
  border-radius: 24px;
  bottom: auto;
  height: 48px;
  overflow: visible;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
  cursor: grab;
  user-select: none;
  flex-shrink: 0;
}

.card-header:active {
  cursor: grabbing;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title {
  font-size: 13px;
  font-weight: 600;
  color: #444;
  letter-spacing: 0.5px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 2px;
}

.header-btn {
  color: #888 !important;
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.resize-handle {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 6px;
  cursor: col-resize;
  z-index: 10;
}

.resize-handle:hover {
  background: rgba(24, 144, 255, 0.15);
}

.collapsed-pill {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 48px;
  cursor: pointer;
  color: #888;
  transition: color 0.2s;
}

.collapsed-pill:hover {
  color: #444;
}
</style>
