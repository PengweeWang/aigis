import { ref, onUnmounted } from 'vue'
import { useMessagesStore } from '../stores/messages'

export function useSSE() {
  const isConnected = ref(false)
  let eventSource = null
  let reconnectTimer = null

  function connect() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    clearTimeout(reconnectTimer)

    eventSource = new EventSource('/global/event')

    eventSource.onopen = () => {
      isConnected.value = true
    }

    eventSource.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        const messagesStore = useMessagesStore()
        messagesStore.applySSEEvent(msg)
      } catch { /* ignore malformed events */ }
    }

    eventSource.onerror = () => {
      isConnected.value = false
      eventSource?.close()
      eventSource = null
      reconnectTimer = setTimeout(connect, 3000)
    }
  }

  function disconnect() {
    clearTimeout(reconnectTimer)
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isConnected.value = false
  }

  return { isConnected, connect, disconnect }
}
