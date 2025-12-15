<template>
  <nav class="stepper" aria-label="Wizard steps">
    <button
      v-for="step in steps"
      :key="step.id"
      class="step"
      :class="{
        active: step.id === currentStep,
        done: completedSteps.includes(step.id),
        disabled: isDisabled(step.id)
      }"
      type="button"
      :disabled="isDisabled(step.id)"
      @click="$emit('go', step.id)"
    >
      <span class="pill" aria-hidden="true">
        {{ completedSteps.includes(step.id) ? '✓' : step.id }}
      </span>
      <span class="label">{{ step.title }}</span>
    </button>
  </nav>
</template>

<script setup>
const props = defineProps({
  steps: { type: Array, default: () => [] },
  currentStep: { type: Number, default: 1 },
  completedSteps: { type: Array, default: () => [] },
  unlockedSteps: { type: Array, default: () => [] }
})

defineEmits(['go'])

function isDisabled(stepId) {
  // Allow navigating back anytime. Forward navigation depends on what the app considers "unlocked".
  if (stepId <= props.currentStep) return false
  return !props.unlockedSteps.includes(stepId)
}
</script>

<style scoped>
.stepper {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  background: rgba(255,255,255,0.01);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.step:hover:not(.disabled) {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.step.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.step.active {
  border-color: var(--accent);
  background: rgba(20, 184, 166, 0.08);
  color: var(--text-primary);
}

.step.done {
  border-color: rgba(45, 212, 191, 0.6);
}

.pill {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid var(--border-medium);
  color: var(--text-primary);
  font-size: 0.8rem;
  font-weight: 650;
}

.step.active .pill {
  border-color: var(--accent);
  color: var(--accent-light);
}

.label {
  font-size: 0.85rem;
  font-weight: 600;
}
</style>


