<template>
  <div class="question-dock">
    <div v-if="hasMultipleQuestions" class="question-dock-tabs">
      <button
        v-for="(_, ti) in questions"
        :key="ti"
        class="q-tab"
        :class="{ active: currentTab === ti }"
        @click="$emit('update:currentTab', ti)"
      >{{ ti + 1 }}</button>
    </div>
    <div class="question-dock-header">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>
      </svg>
      <span>{{ currentQuestion.header || currentQuestion.question || '智能体需要确认' }}</span>
    </div>
    <div v-if="currentQuestion.question && currentQuestion.question !== currentQuestion.header" class="question-dock-text">{{ currentQuestion.question }}</div>
    <div v-if="currentQuestion.options?.length" class="question-dock-options">
      <button
        v-for="(opt, oi) in currentQuestion.options"
        :key="oi"
        class="question-option"
        :class="{ selected: selectedAnswer === opt.label }"
        @click="$emit('select-option', opt.label)"
      >
        <span class="q-radio" :class="{ checked: selectedAnswer === opt.label }"></span>
        <span class="q-label">{{ opt.label }}</span>
        <span v-if="opt.description" class="q-desc">{{ opt.description }}</span>
      </button>
      <button
        class="question-option"
        :class="{ selected: showCustomInput }"
        @click="$emit('select-custom')"
      >
        <span class="q-radio" :class="{ checked: showCustomInput }"></span>
        <span class="q-label">输入自定义答案</span>
        <span v-if="freeformAnswer" class="q-desc">{{ freeformAnswer }}</span>
      </button>
    </div>
    <div v-if="showCustomInput" class="question-dock-input">
      <textarea
        ref="questionTextareaRef"
        :value="freeformAnswer"
        class="question-textarea"
        placeholder="输入回答..."
        rows="2"
        @input="$emit('update:freeformAnswer', $event.target.value)"
      ></textarea>
    </div>
    <div v-else-if="!currentQuestion.options?.length" class="question-dock-input">
      <textarea
        :value="freeformAnswer"
        class="question-textarea"
        placeholder="输入回答..."
        rows="2"
        @input="$emit('update:freeformAnswer', $event.target.value)"
      ></textarea>
    </div>
    <div class="question-dock-actions">
      <button class="q-btn q-btn-cancel" @click="$emit('cancel')">取消</button>
      <button class="q-btn q-btn-submit" :disabled="!canSubmit" @click="$emit('submit')">确认</button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  questions: { type: Array, required: true },
  currentQuestion: { type: Object, required: true },
  hasMultipleQuestions: { type: Boolean, default: false },
  currentTab: { type: Number, default: 0 },
  selectedAnswer: { type: String, default: '' },
  freeformAnswer: { type: String, default: '' },
  showCustomInput: { type: Boolean, default: false },
  canSubmit: { type: Boolean, default: false },
})

defineEmits([
  'update:currentTab',
  'select-option',
  'select-custom',
  'update:freeformAnswer',
  'cancel',
  'submit',
])
</script>

<style scoped>
.question-dock {
  padding: 12px 14px;
  border-top: 1px solid #e8e8e8;
  background: linear-gradient(135deg, #fefcf5, #fef9e7);
}
.question-dock-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #d48806;
  margin-bottom: 8px;
}
.question-dock-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}
.q-tab {
  width: 24px; height: 24px;
  border-radius: 50%;
  border: 1px solid #e8e8e8;
  background: #fff;
  color: #999;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.q-tab.active { background: #d48806; color: #fff; border-color: #d48806; }
.q-tab:hover:not(.active) { border-color: #f0c040; }
.question-dock-text {
  font-size: 11px;
  color: #666;
  margin-bottom: 8px;
  line-height: 1.5;
}
.question-dock-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}
.question-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
  font-size: 12px;
}
.question-option:hover { border-color: #f0c040; background: #fffef5; }
.question-option.selected { border-color: #d48806; background: #fff8e1; }
.q-radio {
  width: 14px; height: 14px;
  border-radius: 50%;
  border: 2px solid #d9d9d9;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}
.q-radio.checked { border-color: #d48806; }
.q-radio.checked::after {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #d48806;
}
.q-label { font-weight: 500; color: #333; }
.q-desc { color: #999; font-size: 11px; }
.question-dock-input { margin-bottom: 8px; }
.question-textarea {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  font-family: inherit;
  outline: none;
  resize: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.question-textarea:focus { border-color: #d48806; box-shadow: 0 0 0 2px rgba(212, 136, 6, 0.1); }
.question-dock-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}
.q-btn {
  padding: 6px 14px;
  border-radius: 6px;
  border: none;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.q-btn-cancel { background: #f0f0f0; color: #666; }
.q-btn-cancel:hover { background: #e4e4e4; }
.q-btn-submit { background: #d48806; color: #fff; }
.q-btn-submit:hover { background: #e8a020; }
.q-btn-submit:disabled { background: #d9d9d9; color: #fff; cursor: not-allowed; }
</style>
