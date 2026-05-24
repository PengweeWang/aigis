<template>
  <div id="map-container" class="map-container"></div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import AMapLoader from '@amap/amap-jsapi-loader';

const map = ref(null);
const markers = ref([]);
const polylines = ref([]);
let AMapInstance = null;

const addModeEnabled = ref(false);
const userMarkers = ref([]);
const labelCounter = ref(0);
const freedLabels = ref([]);

const MARKER_PALETTE = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f97316']
let colorIndex = 0
const labelColorMap = {}

function getNextLabel() {
  if (freedLabels.value.length > 0) {
    freedLabels.value.sort((a, b) => a.localeCompare(b));
    return freedLabels.value.shift();
  }
  const n = labelCounter.value;
  labelCounter.value++;
  let label = '';
  let count = n;
  do {
    label = String.fromCharCode(65 + (count % 26)) + label;
    count = Math.floor(count / 26) - 1;
  } while (count >= 0);
  return label;
}

function getMarkerColor() {
  const c = MARKER_PALETTE[colorIndex % MARKER_PALETTE.length]
  colorIndex++
  return c
}

function onMapClick(e) {
  if (!addModeEnabled.value || !AMapInstance) return;
  const lng = e.lnglat.getLng();
  const lat = e.lnglat.getLat();
  const label = getNextLabel();
  const uid = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  const color = labelColorMap[label] || getMarkerColor()
  labelColorMap[label] = color
  const contentDiv = document.createElement('div');
  contentDiv.className = 'amap-user-marker';
  contentDiv.dataset.amapUid = uid;
  contentDiv.style.setProperty('--marker-color', color);
  contentDiv.innerHTML = '<div class="amap-user-marker-body"><span class="amap-user-marker-label">' + label + '</span></div><div class="amap-user-marker-arrow"></div><span class="amap-user-marker-close">&times;</span>';
  const marker = new AMapInstance.Marker({
    position: [lng, lat],
    content: contentDiv,
    offset: new AMapInstance.Pixel(-14, -33),
    zIndex: 120,
  });
  map.value.add(marker);
  userMarkers.value.push({ label, marker, position: [lng, lat], uid });
}

function handleMarkerCloseClick(ev) {
  const closeBtn = ev.target.closest('.amap-user-marker-close');
  if (!closeBtn) return;
  const markerEl = closeBtn.closest('[data-amap-uid]');
  if (!markerEl) return;
  const uid = markerEl.dataset.amapUid;
  const idx = userMarkers.value.findIndex(u => u.uid === uid);
  if (idx !== -1) {
    map.value.remove(userMarkers.value[idx].marker);
    freedLabels.value.push(userMarkers.value[idx].label);
    userMarkers.value.splice(idx, 1);
  }
}

function enableAddMode() {
  addModeEnabled.value = true;
  if (map.value) {
    map.value.setDefaultCursor('crosshair');
  }
}

function disableAddMode() {
  addModeEnabled.value = false;
  if (map.value) {
    map.value.setDefaultCursor('');
  }
}

function toggleAddMode() {
  if (addModeEnabled.value) {
    disableAddMode();
  } else {
    enableAddMode();
  }
}

function getAddModeEnabled() {
  return addModeEnabled.value;
}

function getUserPoints() {
  return userMarkers.value.map(({ label, position }) => ({
    label,
    lng: position[0],
    lat: position[1],
  }));
}

function clearUserPoints() {
  userMarkers.value.forEach(({ marker }) => {
    map.value.remove(marker);
  });
  userMarkers.value = [];
  labelCounter.value = 0;
  freedLabels.value = [];
  colorIndex = 0
  for (const k of Object.keys(labelColorMap)) delete labelColorMap[k]
}

let closeClickListenerCleanup = null;

onMounted(() => {
  window._AMapSecurityConfig = {
    securityJsCode: import.meta.env.VITE_AMAP_SECURITY_CODE,
  };

  AMapLoader.load({
    key: import.meta.env.VITE_AMAP_KEY,
    version: '2.0',
    plugins: ['AMap.Scale', 'AMap.ToolBar'],
  }).then((AMap) => {
    AMapInstance = AMap;
    AMap.getConfig().appname = 'amap-jsapi-skill';

    map.value = new AMap.Map('map-container', {
      viewMode: '2D',
      zoom: 11,
      center: [116.39, 39.90],
      mapStyle: 'amap://styles/normal',
    });

    map.value.addControl(new AMap.Scale());
    map.value.addControl(new AMap.ToolBar({ position: 'RT' }));

    map.value.on('click', onMapClick);

    const containerEl = document.getElementById('map-container');
    const handler = handleMarkerCloseClick;
    if (containerEl) {
      containerEl.addEventListener('click', handler);
      closeClickListenerCleanup = () => containerEl.removeEventListener('click', handler);
    }
  });
});

const addMarker = (position, options = {}) => {
  if (!map.value || !AMapInstance) return;
  const marker = new AMapInstance.Marker({
    position,
    ...options,
  });
  map.value.add(marker);
  markers.value.push(marker);
  return marker;
};

const addPolyline = (path, options = {}) => {
  if (!map.value || !AMapInstance) return;
  const polyline = new AMapInstance.Polyline({
    path,
    ...options,
  });
  map.value.add(polyline);
  polylines.value.push(polyline);
  return polyline;
};

const setCenter = (center, zoom) => {
  if (!map.value) return;
  map.value.setCenter(center);
  if (zoom) {
    map.value.setZoom(zoom);
  }
};

const clearMarkers = () => {
  if (!map.value) return;
  map.value.remove(markers.value);
  markers.value = [];
};

const clearPolylines = () => {
  if (!map.value) return;
  map.value.remove(polylines.value);
  polylines.value = [];
};

defineExpose({
  addMarker,
  addPolyline,
  setCenter,
  clearMarkers,
  clearPolylines,
  enableAddMode,
  disableAddMode,
  toggleAddMode,
  getAddModeEnabled,
  getUserPoints,
  clearUserPoints,
});

onUnmounted(() => {
  if (closeClickListenerCleanup) {
    closeClickListenerCleanup();
  }
  if (map.value) {
    map.value.destroy();
  }
});
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
}
</style>

<style>
.amap-user-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: marker-pop 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
  pointer-events: auto;
}

.amap-user-marker-body {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--marker-color);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.22), 0 1px 2px rgba(0, 0, 0, 0.1);
  border: 2.5px solid #fff;
  position: relative;
  z-index: 1;
}

.amap-user-marker-label {
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.18);
  user-select: none;
}

.amap-user-marker-arrow {
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 7px solid var(--marker-color);
  margin-top: -2px;
  position: relative;
  z-index: 0;
}

.amap-user-marker-close {
  position: absolute;
  top: -2px;
  right: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #fff;
  color: #999;
  font-size: 9px;
  font-weight: 700;
  line-height: 14px;
  text-align: center;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  z-index: 5;
  opacity: 0;
  transform: scale(0.8);
  transition: opacity 0.2s ease, transform 0.2s ease, color 0.15s, border-color 0.15s, background 0.15s;
  user-select: none;
}

.amap-user-marker:hover .amap-user-marker-close {
  opacity: 1;
  transform: scale(1);
}

.amap-user-marker-close:hover {
  color: #fff;
  background: #ff4d4f;
  border-color: #ff4d4f;
  box-shadow: 0 2px 6px rgba(255, 77, 79, 0.35);
}

@keyframes marker-pop {
  0% {
    transform: scale(0) translateY(8px);
    opacity: 0;
  }
  60% {
    transform: scale(1.1) translateY(-1px);
    opacity: 1;
  }
  100% {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}
</style>