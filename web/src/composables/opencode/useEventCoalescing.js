// web/src/composables/opencode/useEventCoalescing.js

export function useEventCoalescing({ processEvent }) {
  let flushTimer = null
  let eventQueue = []
  const staleDeltas = new Set()
  const coalescedKeys = new Map()

  function coalesceKey(payload) {
    const p = payload.properties || {}
    if (payload.type === 'session.status') return `ss:${p.sessionID}`
    if (payload.type === 'message.part.updated') {
      const part = p.part
      if (!part) return
      return `mpu:${part.messageID}:${part.id}`
    }
  }

  function pushEvent(payload) {
    const k = coalesceKey(payload)
    if (k) {
      const i = coalescedKeys.get(k)
      if (i !== undefined) {
        eventQueue[i] = payload
        if (payload.type === 'message.part.updated') {
          const part = payload.properties?.part
          if (part) staleDeltas.add(`${part.messageID}:${part.id}`)
        }
        scheduleFlush()
        return
      }
      coalescedKeys.set(k, eventQueue.length)
    } else if (payload.type === 'message.part.delta') {
      const p = payload.properties || {}
      if (staleDeltas.has(`${p.messageID}:${p.partID}`)) return
    }
    eventQueue.push(payload)
    scheduleFlush()
  }

  function scheduleFlush() {
    if (flushTimer) return
    flushTimer = setTimeout(flushEvents, 16)
  }

  function flushEvents() {
    flushTimer = null
    if (eventQueue.length === 0) return
    const batch = eventQueue
    eventQueue = []
    coalescedKeys.clear()
    staleDeltas.clear()
    for (const payload of batch) {
      processEvent(payload)
    }
  }

  function flushImmediate() {
    if (flushTimer) {
      clearTimeout(flushTimer)
      flushTimer = null
    }
    flushEvents()
  }

  return { pushEvent, flushImmediate }
}
