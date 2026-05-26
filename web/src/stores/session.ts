import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Use relative paths — Vite proxy handles routing to opencode (4096)
const API = ''

export const useSessionStore = defineStore('session', () => {
  const sessionId = ref(null)
  /** @type {import('vue').Ref<import('../lib/contracts').ModelOption[]>} */
  const models = ref([])
  const selectedModel = ref('')
  const isLoadingModels = ref(false)
  const isConnecting = ref(false)
  const serverVersion = ref('')

  const hasSession = computed(() => !!sessionId.value)

  async function checkHealth() {
    try {
      const resp = await fetch(`/global/health`)
      if (resp.ok) {
        const data = await resp.json()
        serverVersion.value = data.version || ''
        return true
      }
    } catch {
      // server not available
    }
    return false
  }

  async function fetchModels() {
    isLoadingModels.value = true
    try {
      const resp = await fetch(`/config/providers`)
      if (!resp.ok) return
      const data = await resp.json()
      /** @type {import('../lib/contracts').ModelOption[]} */
      const options = []
      for (const provider of (data.providers || [])) {
        for (const model of Object.values(provider.models || {})) {
          options.push({
            value: model.id,
            providerID: model.providerID || provider.id,
            label: `${provider.name} - ${model.name || model.id}`,
          })
        }
      }
      if (options.length > 0) {
        models.value = options
        selectedModel.value = options.find(o => o.value === 'minimax-m2.5-free')?.value || options[0].value
      }
    } finally {
      isLoadingModels.value = false
    }
  }

  async function createSession() {
    try {
      const resp = await fetch(`/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      if (resp.ok) {
        const session = await resp.json()
        sessionId.value = session.id
        return session.id
      }
    } catch {
      // fail silently
    }
    return null
  }

  function setModel(modelId) {
    selectedModel.value = modelId
  }

  function getModelConfig() {
    const model = models.value.find(o => o.value === selectedModel.value)
    return model ? { providerID: model.providerID, modelID: model.value } : undefined
  }

  return {
    sessionId,
    models,
    selectedModel,
    isLoadingModels,
    isConnecting,
    serverVersion,
    hasSession,
    checkHealth,
    fetchModels,
    createSession,
    setModel,
    getModelConfig,
  }
})
