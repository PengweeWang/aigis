// web/src/utils/mapRenderer.js

const POLY_COLORS = ['#6366f1', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f97316', '#8b5cf6', '#ef4444']

let polyColorIndex = 0
let distColorIndex = 0

export function resetColorIndices() {
  polyColorIndex = 0
  distColorIndex = 0
}

export function isValidCoord(lng, lat) {
  return lng != null && lat != null && !isNaN(lng) && !isNaN(lat)
}

export function calcZoom(lng1, lat1, lng2, lat2) {
  const spanLng = Math.abs(lng1 - lng2) * 1.1
  const spanLat = Math.abs(lat1 - lat2) * 1.1
  const zLng = Math.log2(360 / Math.max(spanLng, 0.001))
  const zLat = Math.log2(180 / Math.max(spanLat, 0.001))
  return Math.max(3, Math.min(18, Math.floor(Math.min(zLng, zLat))))
}

export function renderData(data, mc) {
  if (!data || !data.type || !data.data || !data.data.length) return
  if (!mc) return

  if (data.type === 'points') {
    data.data.forEach(item => {
      const loc = item.location
      if (isValidCoord(loc?.lng, loc?.lat)) {
        mc.addMarker([loc.lng, loc.lat], {
          title: item.formatted_address || item.address || '',
          label: { content: item.formatted_address || item.address || '点位', direction: 'top' },
        })
      }
    })
    const first = data.data[0]?.location
    if (isValidCoord(first?.lng, first?.lat)) mc.setCenter([first.lng, first.lat], 14)
  } else if (data.type === 'polyline') {
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
    data.data.forEach((item) => {
      if (isValidCoord(item.origin?.lng, item.origin?.lat)) {
        mc.addMarker([item.origin.lng, item.origin.lat], { title: item.origin.address || '起点', label: { content: item.origin.address || '起点', direction: 'top' } })
      }
      if (isValidCoord(item.destination?.lng, item.destination?.lat)) {
        mc.addMarker([item.destination.lng, item.destination.lat], { title: item.destination.address || '终点', label: { content: item.destination.address || '终点', direction: 'top' } })
      }
      if (isValidCoord(item.origin?.lng, item.origin?.lat) && isValidCoord(item.destination?.lng, item.destination?.lat)) {
        const color = POLY_COLORS[distColorIndex % POLY_COLORS.length]
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
