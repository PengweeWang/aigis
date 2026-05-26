import { defineStore } from 'pinia'
import { ref } from 'vue'


export const useDataWebSocket = defineStore('dataWs', () => {
  const isConnected = ref(false)
  /** @type {WebSocket | null} */
  let ws = null
  let reconnectTimer = null

  /** @type {((data: import('../lib/contracts').WsMessage) => void) | null} */
  let onData = null

  /**
   * @param {(data: import('../lib/contracts').WsMessage) => void} handler
   */
  function connect(handler) {
    onData = handler
    if (ws && ws.readyState === WebSocket.OPEN) return
    _doConnect()
  }

  function _doConnect() {
    try {
      // Connect directly to data server port 8000 (forwarded by VS Code from container).
      // Fall back to Vite proxy (port from location) if direct connection isn't available.
      const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
      const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const port = 8000
      ws = new WebSocket(`${protocol}//${hostname}:${port}/ws/data`)
    } catch {
      _scheduleReconnect()
      return
    }

    ws.onopen = () => {
      isConnected.value = true
    }

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.type && onData) {
          onData(data)
        }
      } catch { /* ignore */ }
    }

    ws.onclose = () => {
      isConnected.value = false
      _scheduleReconnect()
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function _scheduleReconnect() {
    clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(_doConnect, 1000)
  }

  function disconnect() {
    clearTimeout(reconnectTimer)
    if (ws) {
      ws.onopen = null
      ws.onmessage = null
      ws.onerror = null
      ws.onclose = null
      ws.close()
      ws = null
    }
    isConnected.value = false
  }

  return { isConnected, connect, disconnect }
})
