import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useStreamingStore = defineStore('streaming', () => {
  const isStreaming = ref(false)
  const currentAssistantId = ref(null)
  /** @type {import('vue').Ref<Record<string, string>>} */
  const partTexts = ref({})
  /** @type {import('vue').Ref<import('../lib/contracts').Part[]>} */
  const pendingToolCalls = ref([])

  function startMessage(messageId) {
    isStreaming.value = true
    currentAssistantId.value = messageId
    partTexts.value = {}
    pendingToolCalls.value = []
  }

  function applyPartDelta(messageId, partId, delta) {
    if (messageId !== currentAssistantId.value) return
    if (!partTexts.value[partId]) {
      partTexts.value[partId] = ''
    }
    partTexts.value[partId] += delta
  }

  /** @param {import('../lib/contracts').Part} part */
  function applyPartUpdated(part) {
    if (!part.messageID) return

    if (part.type === 'text' && part.text) {
      if (!partTexts.value[part.id]) {
        partTexts.value[part.id] = part.text
      }
    }

    if (part.type === 'tool') {
      // Update existing tool call or add new one
      const existing = pendingToolCalls.value.findIndex(tc => tc.id === part.id)
      if (existing >= 0) {
        pendingToolCalls.value[existing] = part
      } else {
        pendingToolCalls.value.push(part)
      }
    }
  }

  function getStreamedText() {
    return Object.values(partTexts.value).join('')
  }

  function finalizeMessage(messageId) {
    isStreaming.value = false
    currentAssistantId.value = null
    partTexts.value = {}
    pendingToolCalls.value = []
  }

  return {
    isStreaming,
    currentAssistantId,
    partTexts,
    pendingToolCalls,
    startMessage,
    applyPartDelta,
    applyPartUpdated,
    getStreamedText,
    finalizeMessage,
  }
})
