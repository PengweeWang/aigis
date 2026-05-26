import MarkdownIt from 'markdown-it'
import Shiki from '@shikijs/markdown-it'
import katex from 'katex'

// Simple KaTeX plugin inline — avoids extra deps
function katexPlugin(md) {
  const defaultRender = md.renderer.rules.fence?.bind(md.renderer.rules)
  md.renderer.rules.fence = (tokens, idx, options, env, slf) => {
    const token = tokens[idx]
    const info = token.info.trim()
    // Mermaid diagrams — delegate to mermaid render
    if (info === 'mermaid') {
      return `<div class="mermaid-container" data-mermaid="${encodeURIComponent(token.content)}"><span class="mermaid-loading">图表加载中...</span></div>`
    }
    // KaTeX math blocks
    if (info === 'math' || info === 'katex') {
      try {
        const html = katex.renderToString(token.content, { displayMode: true, throwOnError: false })
        return `<div class="math-block">${html}</div>`
      } catch {
        return `<pre><code>${md.utils.escapeHtml(token.content)}</code></pre>`
      }
    }
    // Delegate to Shiki for code
    if (defaultRender) return defaultRender(tokens, idx, options, env, slf)
    return `<pre><code>${md.utils.escapeHtml(token.content)}</code></pre>`
  }

  // Inline KaTeX: $...$ and $$...$$
  const defaultText = md.renderer.rules.text?.bind(md.renderer.rules)
  md.renderer.rules.text = (tokens, idx, options, env, slf) => {
    const text = tokens[idx].content
    // Replace inline math $...$ but not $$
    const hasInlineMath = /\$[^$]+\$/.test(text)
    if (!hasInlineMath) {
      return defaultText ? defaultText(tokens, idx, options, env, slf) : md.utils.escapeHtml(text)
    }
    return text.replace(/\$([^$]+)\$/g, (_m, formula) => {
      try {
        return katex.renderToString(formula, { displayMode: false, throwOnError: false })
      } catch {
        return _m
      }
    })
  }
}

// WeakMap cache — md instance per no-cache use
let mdInstance = null

function createMarkdownIt() {
  const md = new MarkdownIt({
    html: false,
    breaks: true,
    linkify: true,
    typographer: true,
  })

  md.use(katexPlugin)

  return md
}

/**
 * @returns {Promise<MarkdownIt>}
 */
async function getRenderer() {
  if (mdInstance) return mdInstance

  const md = createMarkdownIt()

  // Shiki with github-light theme
  try {
    md.use(await Shiki({
      themes: {
        light: 'github-light',
      },
      defaultTheme: 'light',
    }))
  } catch (e) {
    console.warn('Shiki init failed, code highlighting disabled:', e)
  }

  mdInstance = md
  return md
}

/**
 * Render markdown to HTML
 * @param {string} src
 * @returns {Promise<string>}
 */
export async function renderMarkdown(src) {
  if (!src) return ''
  const md = await getRenderer()
  return md.render(src)
}

/**
 * Sync render without Shiki (fallback for non-code content)
 * @param {string} src
 * @returns {string}
 */
export function renderMarkdownSync(src) {
  if (!src) return ''
  const md = createMarkdownIt()
  return md.render(src)
}
