<template>
  <div class="selector">
    <div class="selector-header">
      <h3>Bet Types</h3>
      <span v-if="modelValue.length" class="count">{{ modelValue.length }} selected</span>
    </div>
    <div class="selector-body">
      <label
        v-for="betType in betTypes"
        :key="betType.key"
        class="checkbox-item"
        :class="{ disabled: isDisabled(betType.key) }"
        :title="getTooltip(betType.key)"
      >
        <input
          type="checkbox"
          :checked="modelValue.includes(betType.key)"
          :disabled="isDisabled(betType.key)"
          @change="toggleBetType(betType.key)"
        />
        <span class="bet-name">{{ betType.title }}</span>
      </label>
    </div>
    <div v-if="hasCollegeSports" class="selector-footer warning">
      <small>Player props disabled for NCAA sports</small>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { betTypes } from '../data/betTypes.js'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  selectedSports: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const hasCollegeSports = computed(() => {
  return props.selectedSports.some(
    s => s === 'americanfootball_ncaaf' || s === 'basketball_ncaab' || s === 'basketball_wncaab' || s === 'icehockey_ncaa'
  )
})

// If the user had player props selected, auto-remove it when NCAA/college sports are selected
watch(hasCollegeSports, (isCollege) => {
  if (isCollege && props.modelValue.includes('player_props')) {
    emit('update:modelValue', props.modelValue.filter(k => k !== 'player_props'))
  }
})

function isDisabled(key) {
  if (key === 'player_props' && hasCollegeSports.value) {
    return true
  }
  return false
}

function getTooltip(key) {
  if (key === 'player_props' && hasCollegeSports.value) {
    return 'Player props not available for NCAA sports'
  }
  return ''
}

function toggleBetType(key) {
  if (isDisabled(key)) return

  const newValue = props.modelValue.includes(key)
    ? props.modelValue.filter(k => k !== key)
    : [...props.modelValue, key]
  emit('update:modelValue', newValue)
}
</script>

<style scoped>
.selector {
  border-bottom: 1px solid var(--border-light);
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
}

.selector-header h3 {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
}

.count {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.selector-body {
  padding: 8px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
}

.checkbox-item:hover:not(.disabled) {
  background: var(--bg-tertiary);
}

.checkbox-item.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.checkbox-item input {
  accent-color: var(--accent);
}

.bet-name {
  font-size: 0.8125rem;
  color: var(--text-primary);
}

.selector-footer {
  padding: 8px 16px;
  border-top: 1px solid var(--border-light);
}

.selector-footer.warning {
  background: rgba(248, 113, 113, 0.1);
}

.selector-footer small {
  font-size: 0.75rem;
  color: var(--error);
}
</style>
