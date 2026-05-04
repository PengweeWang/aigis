<template>
  <div id="map-container" class="map-container"></div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import AMapLoader from '@amap/amap-jsapi-loader';

const map = ref(null);
const markers = ref([]);
const polylines = ref([]);

onMounted(() => {
  window._AMapSecurityConfig = {
    securityJsCode: import.meta.env.VITE_AMAP_SECURITY_CODE,
  };

  AMapLoader.load({
    key: import.meta.env.VITE_AMAP_KEY,
    version: '2.0',
    plugins: ['AMap.Scale', 'AMap.ToolBar'],
  }).then((AMap) => {
    AMap.getConfig().appname = 'amap-jsapi-skill';

    map.value = new AMap.Map('map-container', {
      viewMode: '2D',
      zoom: 11,
      center: [116.39, 39.90],
      mapStyle: 'amap://styles/normal',
    });

    map.value.addControl(new AMap.Scale());
    map.value.addControl(new AMap.ToolBar({ position: 'RT' }));
  });
});

const addMarker = (position, options = {}) => {
  if (!map.value) return;
  const marker = new AMap.Marker({
    position,
    ...options,
  });
  map.value.add(marker);
  markers.value.push(marker);
  return marker;
};

const addPolyline = (path, options = {}) => {
  if (!map.value) return;
  const polyline = new AMap.Polyline({
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
});

onUnmounted(() => {
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