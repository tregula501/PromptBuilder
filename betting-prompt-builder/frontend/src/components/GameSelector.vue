<template>
  <div class="game-selector">
    <div class="selector-header">
      <h3>Games</h3>
      <div class="header-actions">
        <span v-if="modelValue.length" class="count">{{ modelValue.length }} selected</span>
        <button @click="$emit('fetch')" :disabled="!canFetch || fetchLoading" class="fetch-btn">
          {{ fetchLoading ? 'Loading...' : 'Fetch Games' }}
        </button>
        <button v-if="games.length" @click="selectAll" class="select-all-btn">
          {{ allSelected ? 'Clear All' : 'Select All' }}
        </button>
      </div>
    </div>

    <div class="selector-body">
      <div v-if="manualSports.length" class="manual-entry">
        <div class="manual-title">Manual Matchups (LLM research)</div>
        <div class="manual-row">
          <select v-model="manualSportKey" class="manual-select" aria-label="Manual sport">
            <option v-for="s in manualSports" :key="s.key" :value="s.key">
              {{ s.title }}
            </option>
          </select>
          <input v-model="manualAway" class="manual-input" type="text" placeholder="Away team" />
          <input v-model="manualHome" class="manual-input" type="text" placeholder="Home team" />
          <input v-model="manualTimeLocal" class="manual-time" type="datetime-local" aria-label="Start time (optional)" />
          <button class="manual-add-btn" @click="addManual" :disabled="!canAddManual">Add</button>
        </div>
        <div class="manual-hint">
          Add games here when The Odds API doesn’t support the sport (odds/lines will be researched by the LLM).
        </div>
      </div>

      <div v-if="loading" class="state-message">
        <div class="spinner"></div>
        <span>Loading games...</span>
      </div>

      <div v-else-if="error" class="state-message error">
        <span>{{ error }}</span>
        <button @click="$emit('retry')" class="retry-btn">Try Again</button>
      </div>

      <div v-else-if="!games.length" class="state-message">
        <span>No games available</span>
        <small v-if="manualSports.length">Add manual matchups above, or select other sports and click "Fetch Games"</small>
        <small v-else>Select sports and click "Fetch Games"</small>
      </div>

      <div v-else class="game-list">
        <label
          v-for="game in games"
          :key="game.id"
          class="game-item"
          :class="{ selected: modelValue.some(g => g.id === game.id) }"
        >
          <input
            type="checkbox"
            :checked="modelValue.some(g => g.id === game.id)"
            @change="toggleGame(game)"
          />
          <div class="game-info">
            <div class="teams">
              <span class="away">{{ game.awayTeam }}</span>
              <span class="at">@</span>
              <span class="home">{{ game.homeTeam }}</span>
            </div>
            <div class="meta">
              <span class="sport">{{ game.sportTitle }}</span>
              <span class="time">{{ formatTime(game.commenceTime) }}</span>
            </div>
          </div>
          <div class="odds-info">
            <span v-if="game.bookmakers?.length" class="has-odds">
              {{ game.bookmakers.length }} books
            </span>
            <span v-else class="no-odds">No odds</span>
          </div>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { getSportByKey, isManualOnlySport } from '../data/sports.js'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  games: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
  fetchLoading: { type: Boolean, default: false },
  canFetch: { type: Boolean, default: false },
  selectedSports: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'retry', 'fetch', 'add-manual-game'])

const allSelected = computed(() => {
  return props.games.length > 0 && props.games.every(g => props.modelValue.some(sg => sg.id === g.id))
})

const manualSports = computed(() => {
  const keys = (props.selectedSports || []).filter(k => isManualOnlySport(k))
  return keys.map(k => getSportByKey(k)).filter(Boolean)
})

const manualSportKey = ref('')
const manualAway = ref('')
const manualHome = ref('')
const manualTimeLocal = ref('')

watch(manualSports, (sports) => {
  if (!sports.length) {
    manualSportKey.value = ''
    return
  }
  if (!manualSportKey.value || !sports.some(s => s.key === manualSportKey.value)) {
    manualSportKey.value = sports[0].key
  }
}, { immediate: true })

const canAddManual = computed(() => {
  return Boolean(manualSports.value.length && manualSportKey.value && manualAway.value.trim() && manualHome.value.trim())
})

function addManual() {
  if (!canAddManual.value) return

  let commenceTime = null
  if (manualTimeLocal.value) {
    const dt = new Date(manualTimeLocal.value)
    if (!Number.isNaN(dt.getTime())) commenceTime = dt.toISOString()
  }

  emit('add-manual-game', {
    sportKey: manualSportKey.value,
    awayTeam: manualAway.value.trim(),
    homeTeam: manualHome.value.trim(),
    commenceTime
  })

  manualAway.value = ''
  manualHome.value = ''
  manualTimeLocal.value = ''
}

function toggleGame(game) {
  const isSelected = props.modelValue.some(g => g.id === game.id)
  const newValue = isSelected
    ? props.modelValue.filter(g => g.id !== game.id)
    : [...props.modelValue, game]
  emit('update:modelValue', newValue)
}

function selectAll() {
  emit('update:modelValue', allSelected.value ? [] : [...props.games])
}

function formatTime(isoString) {
  if (!isoString) return 'TBD'
  const date = new Date(isoString)
  if (Number.isNaN(date.getTime())) return 'TBD'
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
}
</script>

<style scoped>
.game-selector {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
}

.selector-header h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.count {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.fetch-btn {
  background: var(--accent);
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.fetch-btn:hover:not(:disabled) {
  background: var(--accent-light);
}

.fetch-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.select-all-btn {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}

.select-all-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.selector-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.state-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 100%;
  color: var(--text-secondary);
  text-align: center;
  padding: 40px;
}

.state-message.error {
  color: var(--error);
}

.manual-entry {
  margin-bottom: 14px;
  padding: 12px;
  border: 1px dashed var(--border-medium);
  border-radius: var(--radius-md);
  background: rgba(20, 184, 166, 0.06);
}

.manual-title {
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.manual-row {
  display: grid;
  grid-template-columns: 140px 1fr 1fr 180px 72px;
  gap: 8px;
}

.manual-select,
.manual-input,
.manual-time {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  font-size: 0.75rem;
}

.manual-add-btn {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
}

.manual-add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.manual-hint {
  margin-top: 8px;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-light);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-btn {
  background: var(--error);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.game-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.game-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
}

.game-item:hover {
  border-color: var(--border-medium);
  box-shadow: var(--shadow-sm);
}

.game-item.selected {
  border-color: var(--accent);
  background: var(--accent-bg);
}

.game-item input {
  accent-color: var(--accent);
}

.game-info {
  flex: 1;
}

.teams {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.teams .away,
.teams .home {
  font-weight: 500;
  color: var(--text-primary);
}

.teams .at {
  color: var(--text-tertiary);
  font-size: 0.8rem;
}

.meta {
  display: flex;
  gap: 12px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.sport {
  color: var(--accent);
}

.odds-info {
  font-size: 0.75rem;
}

.has-odds {
  color: #059669;
}

.no-odds {
  color: var(--error);
}
</style>
