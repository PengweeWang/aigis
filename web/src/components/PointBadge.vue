<template>
  <div class="point-badge-wrapper">
    <n-tooltip>
      <template #trigger>
        <n-button
          class="point-btn"
          :class="{ active: addMode }"
          size="small"
          circle
          @click="$emit('toggle')"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" :stroke="addMode ? '#fff' : '#888'" stroke-width="2">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
            <circle cx="12" cy="9" r="2.5"/>
          </svg>
        </n-button>
      </template>
      地图标注点
    </n-tooltip>
    <n-badge v-if="count > 0" :value="count" :max="99" class="point-badge" />
  </div>
</template>

<script setup>
import { NButton, NBadge, NTooltip } from 'naive-ui'

defineProps({
  addMode: { type: Boolean, default: false },
  count: { type: Number, default: 0 },
})

defineEmits(['toggle'])
</script>

<style scoped>
.point-badge-wrapper {
  position: relative;
  display: inline-flex;
}

.point-btn {
  width: 32px !important;
  height: 32px !important;
  transition: all 0.2s;
}

.point-btn.active {
  background: linear-gradient(135deg, #1890ff, #096dd9) !important;
  color: #fff !important;
}

.point-badge {
  position: absolute;
  top: -4px;
  right: -4px;
}
</style>
