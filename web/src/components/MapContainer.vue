<template>
  <div id="map-container" class="map-container"></div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import AMapLoader from '@amap/amap-jsapi-loader';

const map = ref(null);
const markers = ref([]);
const polylines = ref([]);
const infoWindow = ref(null);
const AMapInstance = ref(null);

// 图标配置
const iconConfigs = {
  start: {
    size: [32, 32],
    image: 'https://webapi.amap.com/theme/v1.3/markers/n/start.png',
    imageSize: [32, 32]
  },
  end: {
    size: [32, 32],
    image: 'https://webapi.amap.com/theme/v1.3/markers/n/end.png',
    imageSize: [32, 32]
  },
  default: {
    size: [24, 34],
    image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
    imageSize: [24, 34]
  }
}

onMounted(() => {
  window._AMapSecurityConfig = {
    securityJsCode: import.meta.env.VITE_AMAP_SECURITY_CODE,
  };

  AMapLoader.load({
    key: import.meta.env.VITE_AMAP_KEY,
    version: '2.0',
    plugins: ['AMap.Scale', 'AMap.ToolBar', 'AMap.InfoWindow'],
  }).then((AMap) => {
    AMapInstance.value = AMap;
    AMap.getConfig().appname = 'amap-jsapi-skill';

    map.value = new AMap.Map('map-container', {
      viewMode: '2D',
      zoom: 11,
      center: [116.39, 39.90],
      mapStyle: 'amap://styles/normal',
    });

    map.value.addControl(new AMap.Scale());
    map.value.addControl(new AMap.ToolBar({ position: 'RT' }));

    // 初始化信息弹窗
    infoWindow.value = new AMap.InfoWindow({
      offset: new AMap.Pixel(0, -30),
      autoMove: true
    });
  });
});

const addMarker = (position, options = {}) => {
  if (!map.value || !AMapInstance.value) return;

  // 处理图标配置
  let markerOptions = { position, ...options }
  if (options.icon && iconConfigs[options.icon]) {
    markerOptions.icon = new AMapInstance.value.Icon(iconConfigs[options.icon])
  }

  const marker = new AMapInstance.value.Marker(markerOptions);

  // 添加点击事件，显示信息弹窗
  if (options.content) {
    marker.on('click', () => {
      showInfoWindow(position, options.content)
    })
  }

  map.value.add(marker);
  markers.value.push(marker);
  return marker;
};

const addPolyline = (path, options = {}) => {
  if (!map.value || !AMapInstance.value) return;
  const polyline = new AMapInstance.value.Polyline({
    path,
    strokeStyle: 'solid',
    lineJoin: 'round',
    lineCap: 'round',
    zIndex: 50,
    ...options,
  });
  map.value.add(polyline);
  polylines.value.push(polyline);

  // 添加点击事件
  if (options.content) {
    polyline.on('click', (e) => {
      showInfoWindow(e.lnglat, options.content)
    })
  }

  return polyline;
};

const setCenter = (center, zoom) => {
  if (!map.value) return;
  map.value.setCenter(center);
  if (zoom) {
    map.value.setZoom(zoom);
  }
};

/**
 * 自动适配视野，让所有标记点都显示在可视区域
 * @param {Array} positions 坐标点数组，如果不传则使用所有标记点
 */
const setFitView = (positions) => {
  if (!map.value) return;
  if (positions && positions.length > 0) {
    map.value.setFitView(positions, false, [20, 20, 20, 20], 15)
  } else {
    map.value.setFitView(null, false, [20, 20, 20, 20], 15)
  }
}

/**
 * 显示信息弹窗
 * @param {Array} position 弹窗位置
 * @param {String} content 弹窗内容
 */
const showInfoWindow = (position, content) => {
  if (!map.value || !infoWindow.value) return;
  infoWindow.value.setContent(content)
  infoWindow.value.open(map.value, position)
}

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

/**
 * 清空所有图层（标记点、路径）
 */
const clearAll = () => {
  clearMarkers()
  clearPolylines()
  if (infoWindow.value) {
    infoWindow.value.close()
  }
}

defineExpose({
  addMarker,
  addPolyline,
  setCenter,
  setFitView,
  showInfoWindow,
  clearMarkers,
  clearPolylines,
  clearAll,
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