<template>
  <div class="app-container">
    <MapContainer ref="mapRef" />
    <ChatPanel />
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
}

.app-container {
  position: relative;
  width: 100%;
  height: 100%;
}
</style>