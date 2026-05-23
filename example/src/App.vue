<template>
  <div class="example-wrapper">
    <div class="example-brand">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1890ff" stroke-width="2">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
      </svg>
      <span>OpenCode Chat 示例</span>
    </div>

    <div class="main-layout">
      <OpenCodeChatPanel
        v-model:panelWidth="panelWidth"
        :minPanelWidth="350"
        title="OpenCode Chat"
        serverUrl="http://127.0.0.1:4096"
      />
      <div class="content-placeholder">
        <div class="placeholder-inner">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d0d0d0" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <path d="M3 9h18M9 21V9"/>
          </svg>
          <span>内容区域</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import OpenCodeChatPanel from '../../components/OpenCodeChatPanel.vue'

const panelWidth = ref(Math.round(window.innerWidth * 0.18))
</script>

<style>
.example-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  background: #f0f2f5;
}
.main-layout {
  display: flex;
  height: 100%;
}
.content-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.placeholder-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #d0d0d0;
  font-size: 16px;
  font-weight: 500;
}
.example-brand {
  position: fixed;
  bottom: 20px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  color: #555;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  z-index: 5;
  user-select: none;
}
</style>
