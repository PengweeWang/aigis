<template>
  <n-collapse v-model:value="modelValue">
    <n-collapse-item name="reasoning">
      <template #header>
        <div class="reasoning-header">思考过程</div>
      </template>
      <div class="reasoning-content" v-html="renderedHtml"></div>
    </n-collapse-item>
  </n-collapse>
</template>

<script setup>
import { computed, ref } from 'vue'
import { NCollapse, NCollapseItem } from 'naive-ui'
import { renderMarkdownSync } from '../lib/markdown'
import DOMPurify from 'dompurify'

const props = defineProps({
  content: { type: String, required: true },
  expanded: { type: Boolean, default: false },
})

const modelValue = ref(props.expanded ? ['reasoning'] : [])

const renderedHtml = computed(() => {
  try {
    return DOMPurify.sanitize(renderMarkdownSync(props.content))
  } catch {
    return DOMPurify.sanitize(props.content)
  }
})

</script>

<style scoped>
.reasoning-header {
  font-size: 12px;
  color: #888;
  font-weight: 500;
}

.reasoning-content {
  font-size: 12px;
  color: #666;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>
