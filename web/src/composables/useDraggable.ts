import { ref } from 'vue'

export function useDraggable(elRef, handleRef) {
  const x = ref(0)
  const y = ref(0)
  const isDragging = ref(false)

  let startX = 0
  let startY = 0
  let origX = 0
  let origY = 0

  function onPointerDown(e) {
    isDragging.value = true
    startX = e.clientX
    startY = e.clientY
    origX = x.value
    origY = y.value

    document.addEventListener('pointermove', onPointerMove)
    document.addEventListener('pointerup', onPointerUp)
    e.preventDefault()
  }

  function onPointerMove(e) {
    if (!isDragging.value) return
    const dx = e.clientX - startX
    const dy = e.clientY - startY
    const el = elRef.value?.$el || elRef.value
    if (!el) return

    const rect = el.getBoundingClientRect()
    const viewW = window.innerWidth
    const viewH = window.innerHeight

    let newX = origX + dx
    let newY = origY + dy

    // Clamp to viewport
    newX = Math.max(-rect.left + 40, Math.min(newX, viewW - rect.right + rect.width - 40))
    newY = Math.max(-rect.top + 40, Math.min(newY, viewH - rect.bottom + rect.height - 40))

    x.value = newX
    y.value = newY
  }

  function onPointerUp() {
    isDragging.value = false
    document.removeEventListener('pointermove', onPointerMove)
    document.removeEventListener('pointerup', onPointerUp)
  }

  function attach() {
    const handle = handleRef.value?.$el || handleRef.value
    if (handle) {
      handle.addEventListener('pointerdown', onPointerDown)
    }
  }

  function detach() {
    const handle = handleRef.value?.$el || handleRef.value
    if (handle) {
      handle.removeEventListener('pointerdown', onPointerDown)
    }
    document.removeEventListener('pointermove', onPointerMove)
    document.removeEventListener('pointerup', onPointerUp)
  }

  return { x, y, isDragging, attach, detach }
}
