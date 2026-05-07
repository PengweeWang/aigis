<template>
  <div class="chat-panel">
    <div class="chat-header">
      <h3>GIS 智能体对话</h3>
      <div class="header-actions">
        <div class="mode-toggle">
          <button :class="['mode-btn', mode === 'agent' ? 'active' : '']" @click="mode = 'agent'" title="通过LLM智能调度">智能</button>
          <button :class="['mode-btn', mode === 'direct' ? 'active' : '']" @click="mode = 'direct'" title="直接调用API，更快更稳">直调</button>
        </div>
        <el-tooltip content="新建会话" placement="bottom">
          <el-button class="new-session-btn" :size="'small'" circle @click="createNewSession">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </el-button>
        </el-tooltip>
      </div>
    </div>

    <ElABubbleList ref="bubbleListRef" class="chat-messages">
      <template v-for="msg in messages" :key="msg.id">
        <ElABubble
          v-if="msg.type === 'message'"
          :placement="msg.role === 'user' ? 'end' : 'start'"
          :content="msg.content"
          :typing="msg.role === 'assistant' && msg.typing"
          :loading="msg.loading"
          :is-markdown="msg.role === 'assistant'"
        />
        <ElAThinking
          v-else-if="msg.type === 'reasoning'"
          v-model="msg.expanded"
          title="思考过程"
        >
          <ElAMarkdown :content="msg.content" />
        </ElAThinking>
      </template>
    </ElABubbleList>

    <div class="chat-input-area">
      <div class="input-toolbar">
        <div class="model-select-wrapper" v-if="mode === 'agent'">
          <svg class="model-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
          </svg>
          <select v-model="selectedModel" class="model-select" @change="handleModelChange">
            <option v-for="m in modelOptions" :key="m.value" :value="m.value">
              {{ m.label }}
            </option>
          </select>
        </div>
        <span v-else class="direct-hint">直调模式：输入自然语言，自动匹配技能</span>
      </div>
      <ElASender
        v-model="inputText"
        placeholder="请输入您的问题..."
        @send="handleSend"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, inject } from 'vue'
import { ElABubble, ElABubbleList, ElASender, ElAThinking, ElAMarkdown } from 'element-ai-vue'

const SERVER_URL = ''
const SKILL_API_URL = '/skill-api'
const bubbleListRef = ref(null)
const mapContainer = inject('mapContainer')

const messages = ref([])
const inputText = ref('')
const currentSessionId = ref(null)
const modelOptions = ref([])
const selectedModel = ref('')
const mode = ref('direct')  // 'agent' 或 'direct'

// ========== 意图识别 & 技能匹配 ==========
const SKILL_PATTERNS = [
  { pattern: /天气|气温|下雨|温度/, skill: 'weather_search', extract: (t) => {
    const cityMatch = t.match(/([一-龥]{2,4})(?:今天|明天|的|目前)?(?:天气|气温|温度)/)
    return cityMatch ? { city: cityMatch[1] } : { city: '北京' }
  }},
  { pattern: /搜索|找|查找|附近|哪里有|有没有/, skill: 'poi_keyword_search', extract: (t) => {
    const cityMatch = t.match(/([一-龥]{2,4})的?/)
    const kwMatch = t.match(/(?:搜索|找|查找|哪里有|有没有)([一-龥a-zA-Z]+)/)
    return { keywords: kwMatch ? kwMatch[1] : t.replace(/[搜索找查找哪里有没有]/g, ''), city: cityMatch ? cityMatch[1] : undefined }
  }},
  { pattern: /经纬度|坐标|在哪|位置/, skill: 'geocode', extract: (t) => {
    const addrMatch = t.match(/([一-龥]{2,20})(?:的|的?)(?:经纬度|坐标|在哪|位置)/)
    return { address: addrMatch ? addrMatch[1] : t.replace(/[经纬度坐标在哪位置?？]/g, '') }
  }},
  { pattern: /行政区|有哪些区|区划|有哪些市/, skill: 'district_search', extract: (t) => {
    const areaMatch = t.match(/([一-龥]{2,4})(?:有哪些|的|市)?(?:区|市|行政区|区划)/)
    return { keywords: areaMatch ? areaMatch[1] : t, subdistrict: 1 }
  }},
  { pattern: /多远|距离|多少公里/, skill: 'distance_measure', extract: (t) => {
    return { origin: '', destination: '', _needGeocode: true, _raw: t }
  }},
  { pattern: /怎么走|路线|导航|路径|开车|骑车|步行|骑行/, skill: 'route_planning', extract: (t) => {
    const modeMatch = t.match(/(开车|驾车|步行|走路|骑车|骑行)/)
    const modeMap = { '开车': 'driving', '驾车': 'driving', '步行': 'walking', '走路': 'walking', '骑车': 'cycling', '骑行': 'cycling' }
    return { origin: '', destination: '', mode: modeMatch ? modeMap[modeMatch[1]] : 'driving', _needGeocode: true, _raw: t }
  }},
  { pattern: /坐车|公交|地铁|坐地铁/, skill: 'public_transit_planning', extract: (t) => {
    return { origin: '', destination: '', city: '北京', _needGeocode: true, _raw: t }
  }},
  { pattern: /IP|ip地址/, skill: 'ip_location', extract: (t) => {
    const ipMatch = t.match(/\d+\.\d+\.\d+\.\d+/)
    return { ip: ipMatch ? ipMatch[0] : '' }
  }},
]

function matchSkill(text) {
  for (const sp of SKILL_PATTERNS) {
    if (sp.pattern.test(text)) {
      const params = sp.extract(text)
      return { skill: sp.skill, params }
    }
  }
  return null
}

function formatSkillResult(skill, result) {
  switch (skill) {
    case 'weather_search': {
      const r = result
      let out = `**${r.province || ''} ${r.city || ''} 天气**\n\n`
      if (r.type === 'live' || r.weather) {
        out += `| 项目 | 信息 |\n|------|------|\n`
        out += `| 天气 | ${r.weather || '-'} |\n`
        out += `| 温度 | ${r.temperature || '-'}°C |\n`
        out += `| 风向 | ${r.wind_direction || '-'} ${r.wind_power || '-'} |\n`
        out += `| 湿度 | ${r.humidity || '-'}% |\n`
      }
      if (r.casts) {
        out += `\n**未来天气预报：**\n\n| 日期 | 白天 | 夜间 | 最高温 | 最低温 |\n|------|------|------|--------|--------|\n`
        for (const c of r.casts) {
          out += `| ${c.date} | ${c.day_weather} | ${c.night_weather} | ${c.day_temp}°C | ${c.night_temp}°C |\n`
        }
      }
      return out
    }
    case 'poi_keyword_search':
    case 'poi_around_search': {
      const r = result
      let out = `**找到 ${r.count || 0} 条结果**\n\n`
      const pois = r.pois || []
      for (let i = 0; i < Math.min(pois.length, 8); i++) {
        const p = pois[i]
        out += `${i + 1}. **${p.name}**${p.distance ? ` (${p.distance}米)` : ''}\n   ${p.address || ''}${p.tel ? ` | ${p.tel}` : ''}\n`
      }
      if (pois.length > 8) out += `\n... 共${r.count}条`
      return out
    }
    case 'geocode': {
      const geocodes = result.geocodes || []
      if (!geocodes.length) return '未找到匹配的地址'
      const g = geocodes[0]
      return `**${g.formatted_address}**\n\n| 项目 | 值 |\n|------|------|\n| 坐标 | ${g.location} |\n| 区域编码 | ${g.adcode} |\n| 级别 | ${g.level} |`
    }
    case 'district_search': {
      const ds = result.districts || []
      if (!ds.length) return '未找到匹配的区域'
      let out = `**${ds[0].name}** 下级行政区：\n\n`
      for (const d of ds) {
        const subs = d.districts || []
        if (subs.length) {
          const names = subs.map(s => s.name).join('、')
          out += `${names}\n`
        }
      }
      return out
    }
    case 'route_planning': {
      const r = result
      const dist = (parseFloat(r.distance_m) / 1000).toFixed(1)
      const dur = Math.round(parseInt(r.duration_s) / 60)
      let out = `**${r.mode === 'driving' ? '驾车' : r.mode === 'walking' ? '步行' : '骑行'}路线**\n\n`
      out += `距离: **${dist}km** | 耗时: **${dur}分钟**\n\n`
      const steps = r.steps || []
      for (let i = 0; i < Math.min(steps.length, 10); i++) {
        const s = steps[i]
        if (s.instruction) out += `${i + 1}. ${s.instruction}\n`
      }
      return out
    }
    case 'distance_measure': {
      const r = result
      return `**距离量算**\n\n距离: **${r.distance_km}km** | 耗时: **${r.duration_min}分钟**`
    }
    case 'ip_location': {
      const r = result
      return `**IP 定位**\n\n| 项目 | 值 |\n|------|------|\n| IP | ${r.ip} |\n| 省份 | ${r.province} |\n| 城市 | ${r.city} |\n| 编码 | ${r.adcode} |`
    }
    default:
      return '```json\n' + JSON.stringify(result, null, 2).slice(0, 500) + '\n```'
  }
}

// ========== 原有 opencode 逻辑 ==========
async function checkServerHealth() {
  try {
    const response = await fetch(`${SERVER_URL}/global/health`)
    if (response.ok) {
      const data = await response.json()
      addSystemMessage(`已连接至GIS智能体，版本: ${data.version}`)
      return true
    }
  } catch (error) {
    addSystemMessage('无法连接到服务器，请确保已运行 opencode serve')
  }
  return false
}

async function createSession() {
  try {
    const response = await fetch(`${SERVER_URL}/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
    if (response.ok) {
      const session = await response.json()
      currentSessionId.value = session.id
      return true
    }
  } catch (error) {
    addSystemMessage('创建会话失败')
  }
  return false
}

async function createNewSession() {
  messages.value = []
  if (mode.value === 'agent') {
    await createSession()
  }
  addSystemMessage(mode.value === 'agent' ? '已创建新会话' : '直调模式就绪')
}

function addSystemMessage(text) {
  messages.value.push({
    id: Date.now().toString() + '-system',
    type: 'message',
    role: 'assistant',
    content: text
  })
  scrollToBottom()
}

function addMessage(role, content, extra = {}) {
  messages.value.push({
    id: Date.now().toString() + '-' + role,
    type: 'message',
    role,
    content,
    ...extra
  })
  scrollToBottom()
}

function addReasoningMessage(text) {
  messages.value.push({
    id: Date.now().toString() + '-reasoning',
    type: 'reasoning',
    content: text,
    expanded: false
  })
  scrollToBottom()
}

async function fetchModels() {
  try {
    const response = await fetch(`${SERVER_URL}/config/providers`)
    if (!response.ok) return
    const data = await response.json()
    const options = []
    for (const provider of data.providers || []) {
      for (const model of Object.values(provider.models || {})) {
        options.push({
          value: model.id,
          providerID: model.providerID,
          label: `${provider.name} - ${model.name || model.id}`,
        })
      }
    }
    if (options.length === 0) return
    modelOptions.value = options
    // 默认选 doubao-seed-2.0-lite
    const lite = options.find(o => o.value === 'doubao-seed-2.0-lite')
    selectedModel.value = lite ? lite.value : options[0].value
  } catch {
    // ignore
  }
}

function handleModelChange() {}

function scrollToBottom() {
  nextTick(() => {
    if (bubbleListRef.value?.scrollToBottom) {
      bubbleListRef.value.scrollToBottom()
    }
  })
}

// ========== 发送逻辑 ==========
async function handleSend(text) {
  addMessage('user', text)
  inputText.value = ''

  if (mode.value === 'direct') {
    await handleDirectSend(text)
  } else {
    await handleAgentSend(text)
  }
}

async function handleDirectSend(text) {
  const match = matchSkill(text)
  if (!match) {
    addMessage('assistant', '未能识别您的意图，试试这些：\n- "北京天气"\n- "搜索北京的咖啡店"\n- "天安门的经纬度"\n- "上海市有哪些区"\n- "从天安门到颐和园开车怎么走"')
    return
  }

  const loadingMsg = {
    id: Date.now().toString() + '-loading',
    type: 'message',
    role: 'assistant',
    content: `正在调用 ${match.skill}...`,
    loading: true,
    typing: false
  }
  messages.value.push(loadingMsg)
  scrollToBottom()

  try {
    // 如果需要先地理编码获取坐标
    if (match.params._needGeocode) {
      const geoResult = await resolveGeocodeFromText(match.params._raw || text)
      if (geoResult) {
        match.params.origin = geoResult.origin
        match.params.destination = geoResult.destination
        if (geoResult.city) match.params.city = geoResult.city
      } else {
        messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
        addMessage('assistant', '无法从您的问题中识别起点和终点，请使用更明确的格式，例如："从天安门到颐和园开车怎么走"')
        return
      }
    }

    delete match.params._needGeocode
    delete match.params._raw

    const response = await fetch(`${SKILL_API_URL}/skill/${match.skill}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(match.params)
    })

    messages.value = messages.value.filter(m => m.id !== loadingMsg.id)

    if (response.ok) {
      const data = await response.json()
      if (data.status === 'success') {
        const formatted = formatSkillResult(match.skill, data.result)
        addMessage('assistant', formatted)

        // 在地图上展示结果
        handleMapDisplay(match.skill, data.result)
      } else {
        addMessage('assistant', `调用失败: ${JSON.stringify(data.result)}`)
      }
    } else {
      const err = await response.text()
      addMessage('assistant', `请求失败: ${err}`)
    }
  } catch (error) {
    messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
    addMessage('assistant', `请求失败: ${error.message}`)
  }
}

async function resolveGeocodeFromText(text) {
  // 尝试从文本中提取 "从A到B" 模式
  const fromTo = text.match(/从?([一-龥]{2,15})(?:到|去|→|->)([一-龥]{2,15})/)
  if (!fromTo) return null

  const originName = fromTo[1]
  const destName = fromTo[2]

  try {
    const [originRes, destRes] = await Promise.all([
      fetch(`${SKILL_API_URL}/skill/geocode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: originName })
      }),
      fetch(`${SKILL_API_URL}/skill/geocode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: destName })
      })
    ])

    const originData = await originRes.json()
    const destData = await destRes.json()

    const originLoc = originData?.result?.geocodes?.[0]?.location
    const destLoc = destData?.result?.geocodes?.[0]?.location

    if (originLoc && destLoc) {
      // 尝试提取城市
      const originCity = originData?.result?.geocodes?.[0]?.city
      return { origin: originLoc, destination: destLoc, city: originCity || '北京' }
    }
  } catch (e) {
    // ignore
  }
  return null
}

function handleMapDisplay(skill, result) {
  if (!mapContainer) return

  // 清除旧的标注和路线
  mapContainer.clearMarkers()
  mapContainer.clearPolylines()

  switch (skill) {
    case 'poi_keyword_search':
    case 'poi_around_search': {
      const pois = result.pois || []
      for (const poi of pois.slice(0, 10)) {
        if (poi.location) {
          const [lng, lat] = poi.location.split(',').map(Number)
          mapContainer.addMarker([lng, lat], {
            title: poi.name,
            label: { content: poi.name, direction: 'top' }
          })
        }
      }
      // 定位到第一个结果
      if (pois.length && pois[0].location) {
        const [lng, lat] = pois[0].location.split(',').map(Number)
        mapContainer.setCenter([lng, lat], 14)
      }
      break
    }
    case 'geocode': {
      const geocodes = result.geocodes || []
      if (geocodes.length && geocodes[0].location) {
        const [lng, lat] = geocodes[0].location.split(',').map(Number)
        mapContainer.addMarker([lng, lat], {
          title: geocodes[0].formatted_address,
          label: { content: geocodes[0].formatted_address?.slice(0, 10), direction: 'top' }
        })
        mapContainer.setCenter([lng, lat], 14)
      }
      break
    }
    case 'route_planning': {
      const polyline = result.route_polyline
      if (polyline && polyline.length > 1) {
        const path = polyline.map(p => [p[0], p[1]])
        mapContainer.addPolyline(path, {
          strokeColor: '#3366FF',
          strokeWeight: 6,
          strokeOpacity: 0.8
        })
        // 添加起终点标注
        mapContainer.addMarker(path[0], { title: '起点', label: { content: '起点', direction: 'top' } })
        mapContainer.addMarker(path[path.length - 1], { title: '终点', label: { content: '终点', direction: 'top' } })
        // 自适应视野
        mapContainer.setCenter(path[Math.floor(path.length / 2)], 12)
      }
      break
    }
    case 'district_search': {
      const ds = result.districts || []
      if (ds.length && ds[0].center) {
        const [lng, lat] = ds[0].center.split(',').map(Number)
        mapContainer.setCenter([lng, lat], 9)
      }
      break
    }
  }
}

async function handleAgentSend(text) {
  if (!currentSessionId.value) {
    const created = await createSession()
    if (!created) return
  }

  const loadingMsg = {
    id: Date.now().toString() + '-loading',
    type: 'message',
    role: 'assistant',
    content: '',
    loading: true,
    typing: false
  }
  messages.value.push(loadingMsg)
  scrollToBottom()

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 120000)

  try {
    const modelConfig = selectedModel.value ? (() => {
      const m = modelOptions.value.find(o => o.value === selectedModel.value)
      return m ? { providerID: m.providerID, modelID: m.value } : undefined
    })() : undefined

    const response = await fetch(`${SERVER_URL}/session/${currentSessionId.value}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent: 'gis-orchestrator',
        model: modelConfig,
        parts: [{ type: 'text', text }]
      }),
      signal: controller.signal
    })

    clearTimeout(timeout)

    messages.value = messages.value.filter(m => m.id !== loadingMsg.id)

    if (response.ok) {
      const result = await response.json()
      renderResponseParts(result.parts)
    } else {
      const errorText = await response.text()
      addMessage('assistant', `请求失败: ${errorText}`)
    }
  } catch (error) {
    clearTimeout(timeout)
    messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
    if (error.name === 'AbortError') {
      addMessage('assistant', '请求超时（2分钟），请稍后重试或切换到直调模式。')
    } else {
      addMessage('assistant', `请求失败: ${error.message}`)
    }
  }
}

function renderResponseParts(parts) {
  let reasoningText = ''
  let answerText = ''

  for (const part of parts) {
    if (part.type === 'reasoning') {
      reasoningText += part.text
    } else if (part.type === 'text') {
      answerText += part.text
    }
  }

  if (reasoningText) {
    addReasoningMessage(reasoningText)
  }
  if (answerText) {
    addMessage('assistant', answerText)
  }
  if (!reasoningText && !answerText) {
    addMessage('assistant', '回答内容为空')
  }
}

async function init() {
  const connected = await checkServerHealth()
  if (connected) {
    await fetchModels()
    if (mode.value === 'agent') {
      await createSession()
    }
  }
  addSystemMessage('直调模式已就绪。输入如"北京天气"、"搜索上海咖啡店"、"从天安门到颐和园开车怎么走"')
}

init()
</script>

<style scoped>
.chat-panel {
  position: fixed;
  left: 20px;
  top: 20px;
  bottom: 20px;
  width: 450px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 10;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.chat-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mode-toggle {
  display: inline-flex;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  overflow: hidden;
}

.mode-btn {
  padding: 4px 10px;
  font-size: 12px;
  border: none;
  background: #fff;
  color: #666;
  cursor: pointer;
  transition: all 0.15s;
}

.mode-btn.active {
  background: #409eff;
  color: #fff;
}

.mode-btn:hover:not(.active) {
  background: #f0f0f0;
}

.direct-hint {
  font-size: 12px;
  color: #888;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

:deep(.el-ai-bubble) {
  margin-bottom: 12px;
}

:deep(.el-ai-bubble:last-child) {
  margin-bottom: 0;
}

:deep(.el-ai-thinking) {
  margin-bottom: 12px;
}

.chat-input-area {
  padding: 8px 16px 16px;
  border-top: 1px solid #eee;
  background: #f8f9fa;
}

.input-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.model-select-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  position: relative;
}

.model-icon {
  color: #666;
  flex-shrink: 0;
}

.model-select {
  appearance: none;
  -webkit-appearance: none;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 5px 24px 5px 10px;
  font-size: 12px;
  color: #444;
  background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E") no-repeat right 8px center;
  cursor: pointer;
  outline: none;
  min-width: 140px;
  max-width: 200px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.model-select:hover {
  border-color: #b0b0b0;
}

.model-select:focus {
  border-color: #909399;
  box-shadow: 0 0 0 2px rgba(144, 147, 153, 0.15);
}

.new-session-btn {
  background: radial-gradient(circle at center, #b0b0b0 0%, #d8d8d8 70%, #e8e8e8 100%) !important;
  color: #666 !important;
  border: none !important;
  border-radius: 50% !important;
  width: 32px !important;
  min-width: 32px !important;
  height: 32px !important;
  min-height: 32px !important;
  padding: 0 !important;
  margin: 0 !important;
  line-height: 32px !important;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.new-session-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}
</style>
