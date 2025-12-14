<template>
  <div class="selector">
    <div class="selector-header">
      <h3>Sportsbooks</h3>
      <span v-if="modelValue.length" class="count">{{ modelValue.length }} selected</span>
    </div>
    <div class="selector-body">
      <label v-for="book in sportsbooks" :key="book.key" class="checkbox-item">
        <input
          type="checkbox"
          :checked="modelValue.includes(book.key)"
          @change="toggleSportsbook(book.key)"
        />
        <span class="book-name">{{ book.title }}</span>
        <span v-if="!book.availableInApi" class="manual-badge">Manual</span>
      </label>
    </div>
    <div class="selector-footer">
      <small>Manual sportsbooks require you to research current odds</small>
    </div>
  </div>
</template>

<script setup>
import { sportsbooks } from '../data/sportsbooks.js'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

function toggleSportsbook(key) {
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

.checkbox-item:hover {
  background: var(--bg-tertiary);
}

.checkbox-item input {
  accent-color: var(--accent);
}

.book-name {
  flex: 1;
  font-size: 0.8125rem;
  color: var(--text-primary);
}

.manual-badge {
  font-size: 0.65rem;
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-weight: 600;
}

.selector-footer {
  padding: 8px 16px;
  background: rgba(251, 191, 36, 0.1);
  border-top: 1px solid var(--border-light);
}

.selector-footer small {
  font-size: 0.75rem;
  color: #fbbf24;
}
</style>
