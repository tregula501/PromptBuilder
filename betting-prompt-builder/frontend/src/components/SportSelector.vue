<template>
  <div class="selector">
    <div class="selector-header">
      <h3>Sports</h3>
      <span v-if="modelValue.length" class="count">{{ modelValue.length }} selected</span>
    </div>
    <div class="selector-body">
      <div v-for="sport in sports" :key="sport.key" class="sport-item">
        <!-- Regular sport (no children) -->
        <label v-if="!sport.children" class="checkbox-item">
          <input
            type="checkbox"
            :checked="modelValue.includes(sport.key)"
            @change="toggleSport(sport.key)"
          />
          <span class="sport-name">{{ sport.title }}</span>
          <span class="sport-desc">{{ sport.description }}</span>
        </label>

        <!-- Sport group (with children like Tennis, Golf) -->
        <div v-else class="sport-group">
          <div class="group-header" @click="toggleGroup(sport.key)">
            <span class="expand-icon">{{ expandedGroups[sport.key] ? '▼' : '▶' }}</span>
            <span class="group-name">{{ sport.title }}</span>
            <span class="group-count">({{ getGroupSelectedCount(sport) }}/{{ sport.children.length }})</span>
          </div>
          <div v-if="expandedGroups[sport.key]" class="group-children">
            <label v-for="child in sport.children" :key="child.key" class="checkbox-item">
              <input
                type="checkbox"
                :checked="modelValue.includes(child.key)"
                @change="toggleSport(child.key)"
              />
              <span class="sport-name">{{ child.title }}</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { sports } from '../data/sports.js'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const expandedGroups = reactive({})

function toggleSport(key) {
  const newValue = props.modelValue.includes(key)
    ? props.modelValue.filter(k => k !== key)
    : [...props.modelValue, key]
  emit('update:modelValue', newValue)
}

function toggleGroup(key) {
  expandedGroups[key] = !expandedGroups[key]
}

function getGroupSelectedCount(sport) {
  return sport.children.filter(c => props.modelValue.includes(c.key)).length
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
  max-height: 250px;
  overflow-y: auto;
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

.sport-name {
  flex: 1;
  font-size: 0.8125rem;
  color: var(--text-primary);
}

.sport-desc {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.sport-group {
  margin-bottom: 4px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
}

.group-header:hover {
  background: var(--bg-tertiary);
}

.expand-icon {
  font-size: 0.7rem;
  color: var(--text-tertiary);
}

.group-name {
  flex: 1;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-primary);
}

.group-count {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.group-children {
  padding-left: 24px;
}
</style>
