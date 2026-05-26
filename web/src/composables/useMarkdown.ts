import { ref, watch } from 'vue'
import DOMPurify from 'dompurify'
import { renderMarkdown, renderMarkdownSync } from '../lib/markdown'

export function useMarkdown(srcRef) {
  const html = ref('')
  const loading = ref(false)

  async function update() {
    const src = typeof srcRef === 'function' ? srcRef() : (srcRef?.value ?? srcRef ?? '')
    if (!src) {
      html.value = ''
      return
    }
    loading.value = true
    try {
      const raw = await renderMarkdown(src)
      html.value = DOMPurify.sanitize(raw, {
        ADD_TAGS: ['div'],
        ADD_ATTR: ['class', 'style', 'data-mermaid', 'data-content'],
      })
    } catch {
      // fallback to sync render
      html.value = DOMPurify.sanitize(renderMarkdownSync(src))
    } finally {
      loading.value = false
    }
  }

  if (typeof srcRef !== 'function' && srcRef?.value !== undefined) {
    watch(() => typeof srcRef === 'function' ? '' : (srcRef?.value ?? srcRef), update, { immediate: true })
  }

  return { html, loading, update }
}

/**
 * @param {string} src — plain text (not streaming)
 * @returns {Promise<string>}
 */
export async function renderOnce(src) {
  try {
    const raw = await renderMarkdown(src)
    return DOMPurify.sanitize(raw)
  } catch {
    return DOMPurify.sanitize(renderMarkdownSync(src))
  }
}
