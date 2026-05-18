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

function onMapClick(e) {
  if (!addModeEnabled.value || !AMapInstance) return;
  const lng = e.lnglat.getLng();
  const lat = e.lnglat.getLat();
  const label = getNextLabel();
  const uid = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  const contentDiv = document.createElement('div');
  contentDiv.className = 'amap-user-marker';
  contentDiv.dataset.amapUid = uid;
  contentDiv.innerHTML = '<span class="amap-user-marker-label">' + label + '</span><span class="amap-user-marker-close">×</span>';
  const marker = new AMapInstance.Marker({
    position: [lng, lat],
    content: contentDiv,
    offset: new AMapInstance.Pixel(-15, -15),
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
  position: relative;
  width: 30px;
  height: 30px;
}

.amap-user-marker-label {
  display: flex;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #1890ff;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: 2.5px solid #fff;
  cursor: pointer;
  user-select: none;
}

.amap-user-marker-close {
  position: absolute;
  top: -7px;
  right: -7px;
  width: 17px;
  height: 17px;
  border-radius: 50%;
  background: #ff4d4f;
  color: #fff;
  font-size: 14px;
  line-height: 17px;
  text-align: center;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
  user-select: none;
  transition: background 0.15s;
}

.amap-user-marker-close:hover {
  background: #ff1a1a;
}
</style>