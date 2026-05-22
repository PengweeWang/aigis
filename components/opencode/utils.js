export function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

export function renderMarkdown(text) {
  if (!text) return ''
  let html = escapeHtml(text)

  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const langClass = lang ? ` class="lang-${escapeHtml(lang)}"` : ''
    return `<pre${langClass}><code>${code}</code></pre>`
  })

  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/~~(.+?)~~/g, '<del>$1</del>')

  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')

  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')

  html = html.replace(/^---+\s*$/gm, '<hr>')

  html = html.replace(/^&gt; (.+)$/gm, '<blockquote><p>$1</p></blockquote>')
  html = html.replace(/<\/blockquote>\n<blockquote>/g, '\n')

  html = html.replace(/^\|(.+)\|\n\|[-| :]+\|\n(\|.+\|\n?)+/gm, (match) => {
    const rows = match.trim().split('\n')
    const headerCells = rows[0].slice(1, -1).split('|').map(c => c.trim())
    const bodyRows = rows.slice(2)
    let table = '<table>'
    table += '<thead><tr>' + headerCells.map(c => `<th>${c}</th>`).join('') + '</tr></thead>'
    if (bodyRows.length) {
      table += '<tbody>'
      for (const row of bodyRows) {
        const cells = row.slice(1, -1).split('|').map(c => c.trim())
        table += '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>'
      }
      table += '</tbody>'
    }
    table += '</table>'
    return table
  })

  const parts = html.split(/\n\n+/)
  html = parts.map(p => {
    p = p.trim()
    if (!p) return ''
    if (p.startsWith('<h') || p.startsWith('<pre') || p.startsWith('<ul') || p.startsWith('<ol') || p.startsWith('<table') || p.startsWith('<hr') || p.startsWith('<blockquote')) return p
    p = p.replace(/\n/g, '<br>')
    return `<p>${p}</p>`
  }).join('')

  return html
}

export function formatToolInput(input) {
  if (typeof input === 'string') return input
  try { return JSON.stringify(input, null, 2) } catch { return String(input) }
}

export function truncateOutput(out) {
  if (!out) return ''
  const s = typeof out === 'string' ? out : JSON.stringify(out, null, 2)
  return s.length > 2000 ? s.slice(0, 2000) + '\n... (已截断)' : s
}

const AGENT_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f97316', '#ef4444']
const agentColorMap = {}

export function agentColor(name) {
  if (!name) return '#6366f1'
  if (!agentColorMap[name]) agentColorMap[name] = AGENT_COLORS[Object.keys(agentColorMap).length % AGENT_COLORS.length]
  return agentColorMap[name]
}

const TOOL_STATUS_LABELS = {
  running: '运行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

export function statusLabel(s) {
  return TOOL_STATUS_LABELS[s] || s || '等待中'
}

export const PERMISSION_LABELS = {
  read: '读取文件',
  write: '写入文件',
  command: '执行命令',
  glob: '搜索文件',
  edit: '编辑文件',
  apply_patch: '应用补丁',
  bash: '执行命令',
  webfetch: '访问网页',
}

export function permissionLabel(name) {
  return PERMISSION_LABELS[name] || name || '执行操作'
}

export const VARIANT_LABELS = { low: '低', medium: '中', high: '高', xhigh: '最高' }

export function variantLabel(v) {
  return VARIANT_LABELS[v] || v
}
