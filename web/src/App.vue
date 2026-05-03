<template>
  <div class="app-container">
    <MapContainer />
    <ChatPanel />
  </div>
</template>

<script setup>
import MapContainer from './components/MapContainer.vue'
import ChatPanel from './components/ChatPanel.vue'
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