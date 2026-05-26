<template>
  <div class="app-container">
    <div class="main-layout">
      <OpenCodeChatPanel
        v-model:panelWidth="panelWidth"
        :minPanelWidth="320"
        title="GIS Chat"
        serverUrl="http://127.0.0.1:4096"
        :show-session-history="false"
        :showNewSession="true"
        defaultAgent="gis-orchestrator"
        :getAnnotationPoints="getAnnotationPoints"
        :onNewSession="onNewSession"
      >
        <template #input-toolbar>
          <div class="add-point-wrapper">
            <button
              class="toolbar-btn"
              :class="{ active: pointAddMode }"
              @click="togglePointAddMode"
              :title="pointAddMode ? '关闭标注模式' : '地图标注'"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" :stroke="pointAddMode ? '#fff' : 'currentColor'" stroke-width="2">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                <circle cx="12" cy="9" r="2.5"/>
              </svg>
            </button>
          </div>
        </template>
      </OpenCodeChatPanel>
      <MapContainer ref="mapRef" />
    </div>
    <div class="app-brand">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
        <circle cx="12" cy="9" r="2.5"/>
      </svg>
      <span>GIS AI</span>
    </div>
  </div>
</template>

<script setup>
import { ref, provide, onMounted, onUnmounted } from 'vue'
import OpenCodeChatPanel from './components/OpenCodeChatPanel.vue'
import MapContainer from './components/MapContainer.vue'

const mapRef = ref(null)
const panelWidth = ref(400)

const pointAddMode = ref(false)

provide('mapContainer', {
  addMarker: (...args) => mapRef.value?.addMarker(...args),
  addPolyline: (...args) => mapRef.value?.addPolyline(...args),
  setCenter: (...args) => mapRef.value?.setCenter(...args),
  clearMarkers: (...args) => mapRef.value?.clearMarkers(...args),
  clearPolylines: (...args) => mapRef.value?.clearPolylines(...args),
  enableAddMode: (...args) => mapRef.value?.enableAddMode(...args),
  disableAddMode: (...args) => mapRef.value?.disableAddMode(...args),
  toggleAddMode: (...args) => mapRef.value?.toggleAddMode(...args),
  getAddModeEnabled: (...args) => mapRef.value?.getAddModeEnabled(...args),
  getUserPoints: (...args) => mapRef.value?.getUserPoints(...args),
  clearUserPoints: (...args) => mapRef.value?.clearUserPoints(...args),
})

function togglePointAddMode() {
  if (pointAddMode.value) {
    mapRef.value?.disableAddMode()
  } else {
    mapRef.value?.enableAddMode()
  }
  pointAddMode.value = !pointAddMode.value
}

function getAnnotationPoints() {
  return mapRef.value?.getUserPoints?.() || []
}

function onNewSession() {
  mapRef.value?.clearMarkers?.()
  mapRef.value?.clearPolylines?.()
  mapRef.value?.clearUserPoints?.()
  pointAddMode.value = false
  polyColorIndex = 0
  distColorIndex = 0
}

let ws = null
let wsReconnectTimer = null

function connectWs() {
  if (ws && ws.readyState === WebSocket.OPEN) return
  ws = new WebSocket('ws://127.0.0.1:8000/ws/data')
  ws.onmessage = (e) => {
    try { renderData(JSON.parse(e.data)) } catch {}
  }
  ws.onclose = () => { wsReconnectTimer = setTimeout(connectWs, 1000) }
  ws.onerror = () => ws?.close()
}

function disconnectWs() {
  clearTimeout(wsReconnectTimer)
  if (ws) {
    ws.onclose = null; ws.onmessage = null; ws.onerror = null
    ws.close(); ws = null
  }
}

let polyColorIndex = 0
let distColorIndex = 0

function isValidCoord(lng, lat) {
  return lng != null && lat != null && !isNaN(lng) && !isNaN(lat)
}

function calcZoom(lng1, lat1, lng2, lat2) {
  const spanLng = Math.abs(lng1 - lng2) * 1.1
  const spanLat = Math.abs(lat1 - lat2) * 1.1
  const zLng = Math.log2(360 / Math.max(spanLng, 0.001))
  const zLat = Math.log2(180 / Math.max(spanLat, 0.001))
  return Math.max(3, Math.min(18, Math.floor(Math.min(zLng, zLat))))
}

function renderData(data) {
  if (!data || !data.type || !data.data || !data.data.length) return
  const mc = mapRef.value
  if (!mc) return
  if (data.type === 'points') {
    data.data.forEach(item => {
      const loc = item.location
      if (isValidCoord(loc?.lng, loc?.lat)) {
        mc.addMarker([loc.lng, loc.lat], { title: item.formatted_address || item.address || '', label: { content: item.formatted_address || item.address || '点位', direction: 'top' } })
      }
    })
    const first = data.data[0]?.location
    if (isValidCoord(first?.lng, first?.lat)) mc.setCenter([first.lng, first.lat], 14)
  } else if (data.type === 'polyline') {
    const POLY_COLORS = ['#6366f1', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f97316', '#8b5cf6', '#ef4444']
    data.data.forEach((item, i) => {
      if (i === 0 && item.origin && item.destination) {
        if (isValidCoord(item.origin.lng, item.origin.lat)) {
          mc.addMarker([item.origin.lng, item.origin.lat], { title: item.origin.address || '起点', label: { content: item.origin.address || '起点', direction: 'top' } })
        }
        if (isValidCoord(item.destination.lng, item.destination.lat)) {
          mc.addMarker([item.destination.lng, item.destination.lat], { title: item.destination.address || '终点', label: { content: item.destination.address || '终点', direction: 'top' } })
        }
        return
      }
      const coords = (item.polyline || []).filter(p => isValidCoord(p.lng, p.lat)).map(p => [p.lng, p.lat])
      if (coords.length > 0) {
        const color = POLY_COLORS[polyColorIndex % POLY_COLORS.length]
        mc.addPolyline(coords, { strokeColor: color, strokeWeight: 5 })
        polyColorIndex++
      }
    })
    const meta = data.data[0]
    if (meta?.origin && meta?.destination &&
        isValidCoord(meta.origin.lng, meta.origin.lat) &&
        isValidCoord(meta.destination.lng, meta.destination.lat)) {
      const z = calcZoom(meta.origin.lng, meta.origin.lat, meta.destination.lng, meta.destination.lat)
      mc.setCenter([(meta.origin.lng + meta.destination.lng) / 2, (meta.origin.lat + meta.destination.lat) / 2], z)
    }
  } else if (data.type === 'distance') {
    const DIST_COLORS = ['#6366f1', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f97316', '#8b5cf6', '#ef4444']
    data.data.forEach((item) => {
      if (isValidCoord(item.origin?.lng, item.origin?.lat)) {
        mc.addMarker([item.origin.lng, item.origin.lat], { title: item.origin.address || '起点', label: { content: item.origin.address || '起点', direction: 'top' } })
      }
      if (isValidCoord(item.destination?.lng, item.destination?.lat)) {
        mc.addMarker([item.destination.lng, item.destination.lat], { title: item.destination.address || '终点', label: { content: item.destination.address || '终点', direction: 'top' } })
      }
      if (isValidCoord(item.origin?.lng, item.origin?.lat) && isValidCoord(item.destination?.lng, item.destination?.lat)) {
        const color = DIST_COLORS[distColorIndex % DIST_COLORS.length]
        mc.addPolyline([[item.origin.lng, item.origin.lat], [item.destination.lng, item.destination.lat]], { strokeColor: color, strokeWeight: 3, strokeStyle: 'dashed' })
        distColorIndex++
      }
    })
    const item = data.data[0]
    if (item?.origin && item?.destination &&
        isValidCoord(item.origin.lng, item.origin.lat) &&
        isValidCoord(item.destination.lng, item.destination.lat)) {
      const z = calcZoom(item.origin.lng, item.origin.lat, item.destination.lng, item.destination.lat)
      mc.setCenter([(item.origin.lng + item.destination.lng) / 2, (item.origin.lat + item.destination.lat) / 2], z)
    }
  }
}

onMounted(() => connectWs())
onUnmounted(() => disconnectWs())
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: #f0f2f5;
}

.main-layout {
  display: flex;
  height: 100%;
}

.main-layout > :last-child {
  flex: 1;
  min-width: 0;
}

.app-brand {
  position: fixed;
  bottom: 20px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  color: #555;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  z-index: 5;
  user-select: none;
}

.app-brand svg {
  color: #1890ff;
}

.add-point-wrapper {
  position: relative;
  display: inline-flex;
}

.toolbar-btn {
  width: 28px; height: 28px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f1f3f5;
  color: #555;
  transition: all 0.2s ease;
  padding: 0;
}

.toolbar-btn:hover {
  background: #e5e8eb;
  color: #333;
}

.toolbar-btn.active {
  background: linear-gradient(135deg, #1890ff, #096dd9) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.4);
}

.point-badge {
  position: absolute;
  top: -4px; right: -4px;
  min-width: 16px; height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: #f5222d;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  line-height: 16px;
  text-align: center;
  pointer-events: none;
}
</style>
