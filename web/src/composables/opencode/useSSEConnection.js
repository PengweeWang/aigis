// web/src/composables/opencode/useSSEConnection.js

export function useSSEConnection({ serverUrl, pushEvent, flushImmediate }) {
  let eventSource = null
  let eventReconnectTimer = null

  function connectEventSource() {
    if (eventSource) return
    eventSource = new EventSource(`${serverUrl}/global/event`)
    eventSource.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data)
        const payload = parsed?.payload
        if (!payload) return
        pushEvent(payload)
      } catch {}
    }
    eventSource.onerror = () => {
      flushImmediate()
      disconnectEventSource()
      eventReconnectTimer = setTimeout(connectEventSource, 3000)
    }
  }

  function disconnectEventSource() {
    clearTimeout(eventReconnectTimer)
    if (eventSource) {
      eventSource.onmessage = null; eventSource.onerror = null
      eventSource.close(); eventSource = null
    }
  }

  return { connectEventSource, disconnectEventSource }
}
