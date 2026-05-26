import { ref, onUnmounted } from 'vue'
import { useDataWebSocket } from '../stores/dataWs'

export function useMapDataSocket(mapContainer) {
  const wsStore = useDataWebSocket()
  let cleanup = null

  function renderData(data) {
    if (!data?.type || !data?.data || data.data.length === 0) return
    if (!mapContainer) return

    requestAnimationFrame(() => {
      if (data.type === 'points') {
        data.data.forEach(item => {
          const loc = item.location
          if (loc?.lng != null && loc?.lat != null) {
            const title = item.formatted_address || item.address || ''
            mapContainer.addMarker([loc.lng, loc.lat], {
              title,
              label: { content: title || '点位', direction: 'top' },
            })
          }
        })
        const first = data.data[0]?.location
        if (first) mapContainer.setCenter([first.lng, first.lat], 14)

      } else if (data.type === 'polyline') {
        data.data.forEach((item, index) => {
          if (index === 0 && item.origin && item.destination) {
            if (item.origin.lng != null && item.origin.lat != null) {
              mapContainer.addMarker([item.origin.lng, item.origin.lat], {
                title: item.origin.address || '起点',
                label: { content: item.origin.address || '起点', direction: 'top' },
              })
            }
            if (item.destination.lng != null && item.destination.lat != null) {
              mapContainer.addMarker([item.destination.lng, item.destination.lat], {
                title: item.destination.address || '终点',
                label: { content: item.destination.address || '终点', direction: 'top' },
              })
            }
            return
          }
          const coords = (item.polyline || []).map(p => [p.lng, p.lat])
          if (coords.length > 0) {
            mapContainer.addPolyline(coords, { strokeColor: '#AA00FF', strokeWeight: 5 })
          }
        })
        const meta = data.data[0]
        if (meta?.origin && meta?.destination) {
          const cx = (meta.origin.lng + meta.destination.lng) / 2
          const cy = (meta.origin.lat + meta.destination.lat) / 2
          mapContainer.setCenter([cx, cy], 12)
        }

      } else if (data.type === 'distance') {
        data.data.forEach(item => {
          if (item.origin) {
            mapContainer.addMarker([item.origin.lng, item.origin.lat], {
              title: item.origin.address || '起点',
              label: { content: item.origin.address || '起点', direction: 'top' },
            })
          }
          if (item.destination) {
            mapContainer.addMarker([item.destination.lng, item.destination.lat], {
              title: item.destination.address || '终点',
              label: { content: item.destination.address || '终点', direction: 'top' },
            })
          }
          if (item.origin && item.destination) {
            mapContainer.addPolyline(
              [[item.origin.lng, item.origin.lat], [item.destination.lng, item.destination.lat]],
              { strokeColor: '#FF6B6B', strokeWeight: 3, strokeStyle: 'dashed' },
            )
          }
        })
        const item = data.data[0]
        if (item?.origin && item?.destination) {
          const cx = (item.origin.lng + item.destination.lng) / 2
          const cy = (item.origin.lat + item.destination.lat) / 2
          mapContainer.setCenter([cx, cy], 12)
        }
      }
    })
  }

  function connect() {
    if (!mapContainer) return
    wsStore.connect(renderData)
  }

  function disconnect() {
    wsStore.disconnect()
  }

  return { isConnected: wsStore.isConnected, connect, disconnect }
}
