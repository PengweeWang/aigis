<template>
  <n-select
    :value="selectedModel"
    :options="options"
    :loading="loading"
    size="small"
    placeholder="选择模型"
    :consistent-menu-width="false"
    @update:value="$emit('update:selectedModel', $event)"
  />
</template>

<script setup>
import { computed } from 'vue'
import { NSelect } from 'naive-ui'

const props = defineProps({
  models: { type: Array, default: () => [] },
  selectedModel: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})

defineEmits(['update:selectedModel'])

const options = computed(() =>
  props.models.map(m => ({
    label: m.label,
    value: m.value,
  }))
)
</script>
