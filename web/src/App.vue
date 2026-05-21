<template>
  <div class="app-container">
    <MapContainer ref="mapRef" />
    <ChatPanel />
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
import { ref, provide } from 'vue'
import MapContainer from './components/MapContainer.vue'
import ChatPanel from './components/ChatPanel.vue'

const mapRef = ref(null)

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
</style>
