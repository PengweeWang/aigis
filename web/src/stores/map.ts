import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useMapStore = defineStore('map', () => {
  /** @type {import('vue').Ref<import('../lib/contracts').UserPoint[]>} */
  const userPoints = ref([])
  const addModeEnabled = ref(false)

  function toggleAddMode() {
    addModeEnabled.value = !addModeEnabled.value
  }

  function setAddMode(val) {
    addModeEnabled.value = val
  }

  /** @param {import('../lib/contracts').UserPoint} point */
  function addPoint(point) {
    userPoints.value.push(point)
  }

  /** @param {string} uid */
  function removePoint(uid) {
    userPoints.value = userPoints.value.filter(p => p.uid !== uid)
  }

  function clearUserPoints() {
    userPoints.value = []
  }

  function getUserPointsSerialized() {
    return userPoints.value.map(({ label, lng, lat }) => ({
      label,
      lng,
      lat,
    }))
  }

  return {
    userPoints,
    addModeEnabled,
    toggleAddMode,
    setAddMode,
    addPoint,
    removePoint,
    clearUserPoints,
    getUserPointsSerialized,
  }
})
