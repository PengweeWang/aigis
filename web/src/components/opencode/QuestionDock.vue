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
  padding: 14px 16px;
  border-top: 1px solid #fde68a;
  background: linear-gradient(180deg, #fffbeb 0%, #fefce8 100%);
  flex-shrink: 0;
  user-select: none;
}
.question-dock-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #b45309;
  margin-bottom: 8px;
}
.question-dock-header svg {
  color: #f59e0b;
  flex-shrink: 0;
}
.question-dock-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}
.q-tab {
  width: 26px; height: 26px;
  border-radius: 50%;
  border: 1.5px solid #e5e7eb;
  background: #fff;
  color: #9ca3af;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}
.q-tab:focus-visible {
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.3);
}
.q-tab.active {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff;
  border-color: #d97706;
  box-shadow: 0 1px 3px rgba(245, 158, 11, 0.3);
}
.q-tab:hover:not(.active) {
  border-color: #fcd34d;
  background: #fffbeb;
}
.question-dock-text {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
  line-height: 1.55;
}
.question-dock-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}
.question-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: left;
  font-size: 12px;
  outline: none;
}
.question-option:focus-visible {
  border-color: #f59e0b;
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.15);
}
.question-option:hover { border-color: #fcd34d; background: #fffbeb; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04); }
.question-option.selected { border-color: #d97706; background: #fef3c7; box-shadow: 0 1px 4px rgba(245, 158, 11, 0.12); }
.q-radio {
  width: 16px; height: 16px;
  border-radius: 50%;
  border: 2px solid #d1d5db;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.q-radio.checked { border-color: #d97706; background: #d97706; }
.q-radio.checked::after {
  content: '';
  width: 5px; height: 5px;
  border-radius: 50%;
  background: #fff;
}
.q-label { font-weight: 500; color: #374151; }
.q-desc { color: #9ca3af; font-size: 11px; margin-left: auto; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.question-dock-input { margin-bottom: 10px; }
.question-textarea {
  width: 100%;
  border: 1.5px solid #e5e7eb;
  user-select: text;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12px;
  font-family: inherit;
  outline: none;
  resize: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
  background: #fff;
  line-height: 1.5;
}
.question-textarea:focus {
  border-color: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
}
.question-dock-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.q-btn {
  padding: 7px 16px;
  border-radius: 8px;
  border: none;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}
.q-btn:focus-visible {
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.3);
}
.q-btn-cancel {
  background: #f3f4f6;
  color: #6b7280;
}
.q-btn-cancel:hover {
  background: #e5e7eb;
  color: #374151;
}
.q-btn-cancel:active {
  transform: scale(0.97);
}
.q-btn-submit {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff;
  box-shadow: 0 1px 3px rgba(245, 158, 11, 0.3);
}
.q-btn-submit:hover {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  box-shadow: 0 2px 6px rgba(245, 158, 11, 0.4);
}
.q-btn-submit:active {
  transform: scale(0.97);
}
.q-btn-submit:disabled {
  background: #d1d5db;
  color: #9ca3af;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
