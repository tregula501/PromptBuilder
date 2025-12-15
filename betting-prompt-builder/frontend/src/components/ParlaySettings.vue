<template>
  <div class="selector">
    <div class="selector-header">
      <h3>Settings</h3>
    </div>

    <div class="selector-body">
      <!-- Prompt Options -->
      <div class="setting-group">
        <label class="setting-label">Prompt Mode</label>
        <div class="radio-group">
          <label class="radio-item">
            <input
              type="radio"
              value="standard"
              :checked="modelValue.promptMode === 'standard'"
              @change="updateSetting('promptMode', 'standard')"
            />
            <span>Standard</span>
          </label>
          <label class="radio-item">
            <input
              type="radio"
              value="compact"
              :checked="modelValue.promptMode === 'compact'"
              @change="updateSetting('promptMode', 'compact')"
            />
            <span>Compact</span>
          </label>
        </div>
        <div class="setting-hint">
          Compact removes long examples/frameworks to keep the prompt shorter.
        </div>
      </div>

      <div class="setting-group">
        <label class="setting-label">LLM Output Format</label>
        <div class="radio-group">
          <label class="radio-item">
            <input
              type="radio"
              value="markdown"
              :checked="modelValue.outputFormat === 'markdown'"
              @change="updateSetting('outputFormat', 'markdown')"
            />
            <span>Markdown/Text</span>
          </label>
          <label class="radio-item">
            <input
              type="radio"
              value="json"
              :checked="modelValue.outputFormat === 'json'"
              @change="updateSetting('outputFormat', 'json')"
            />
            <span>Strict JSON</span>
          </label>
        </div>
        <div class="setting-hint">
          JSON is best if you want consistent, parseable results from the LLM.
        </div>
      </div>

      <div class="setting-group">
        <label class="checkbox-item">
          <input
            type="checkbox"
            :checked="modelValue.requireCitations !== false"
            @change="updateSetting('requireCitations', $event.target.checked)"
          />
          <span>Require sources (links + timestamps)</span>
        </label>
      </div>

      <div class="setting-group">
        <label class="setting-label">
          Recent Form Window: last {{ modelValue.lookbackGames || 10 }} games
        </label>
        <div class="range-row single">
          <input
            type="range"
            min="3"
            max="20"
            :value="modelValue.lookbackGames || 10"
            @input="updateSetting('lookbackGames', parseInt($event.target.value))"
          />
          <span class="range-value">{{ modelValue.lookbackGames || 10 }}</span>
        </div>
      </div>

      <div class="setting-group">
        <label class="setting-label">
          Injury/Lineup Freshness: {{ modelValue.injuryFreshnessHours || 24 }} hours
        </label>
        <div class="range-row single">
          <input
            type="range"
            min="6"
            max="168"
            step="6"
            :value="modelValue.injuryFreshnessHours || 24"
            @input="updateSetting('injuryFreshnessHours', parseInt($event.target.value))"
          />
          <span class="range-value">{{ modelValue.injuryFreshnessHours || 24 }}</span>
        </div>
      </div>

      <!-- Bet Style -->
      <div class="setting-group">
        <label class="setting-label">Bet Style</label>
        <div class="radio-group">
          <label class="radio-item">
            <input
              type="radio"
              value="Straight"
              :checked="modelValue.betStyle === 'Straight'"
              @change="updateSetting('betStyle', 'Straight')"
            />
            <span>Straight Bets</span>
          </label>
          <label class="radio-item">
            <input
              type="radio"
              value="Parlay"
              :checked="modelValue.betStyle === 'Parlay'"
              @change="updateSetting('betStyle', 'Parlay')"
            />
            <span>Include Parlays</span>
          </label>
        </div>
      </div>

      <!-- Risk Level -->
      <div class="setting-group">
        <label class="setting-label">Risk Level</label>
        <div class="radio-group vertical">
          <label class="radio-item">
            <input
              type="radio"
              value="conservative"
              :checked="modelValue.riskLevel === 'conservative'"
              @change="updateSetting('riskLevel', 'conservative')"
            />
            <span>Conservative</span>
          </label>
          <label class="radio-item">
            <input
              type="radio"
              value="average"
              :checked="modelValue.riskLevel === 'average'"
              @change="updateSetting('riskLevel', 'average')"
            />
            <span>Average</span>
          </label>
          <label class="radio-item">
            <input
              type="radio"
              value="aggressive"
              :checked="modelValue.riskLevel === 'aggressive'"
              @change="updateSetting('riskLevel', 'aggressive')"
            />
            <span>Aggressive</span>
          </label>
        </div>
      </div>

      <!-- Recommendation Count -->
      <div class="setting-group">
        <label class="setting-label">
          Recommendations: {{ modelValue.recommendationCount }}
        </label>
        <div class="range-row single">
          <input
            type="range"
            min="1"
            max="10"
            :value="modelValue.recommendationCount"
            @input="updateSetting('recommendationCount', parseInt($event.target.value))"
          />
          <span class="range-value">{{ modelValue.recommendationCount }}</span>
        </div>
      </div>

      <!-- Parlay Legs (only shown for Parlay mode) -->
      <div v-if="modelValue.betStyle === 'Parlay'" class="setting-group">
        <label class="setting-label">
          Parlay Legs: {{ modelValue.minLegs }} - {{ modelValue.maxLegs }}
        </label>
        <div class="range-group">
          <div class="range-row">
            <span>Min</span>
            <input
              type="range"
              min="2"
              max="10"
              :value="modelValue.minLegs"
              @input="updateSetting('minLegs', parseInt($event.target.value))"
            />
            <span class="range-value">{{ modelValue.minLegs }}</span>
          </div>
          <div class="range-row">
            <span>Max</span>
            <input
              type="range"
              min="2"
              max="10"
              :value="modelValue.maxLegs"
              @input="updateSetting('maxLegs', parseInt($event.target.value))"
            />
            <span class="range-value">{{ modelValue.maxLegs }}</span>
          </div>
        </div>
      </div>

      <!-- Odds Range -->
      <div class="setting-group">
        <label class="setting-label">
          Odds Range: {{ formatOdds(modelValue.minOdds) }} to {{ formatOdds(modelValue.maxOdds) }}
        </label>
        <div class="range-group">
          <div class="range-row">
            <span>Min</span>
            <input
              type="range"
              min="-400"
              max="500"
              step="25"
              :value="modelValue.minOdds"
              @input="updateSetting('minOdds', parseInt($event.target.value))"
            />
            <span class="range-value">{{ formatOdds(modelValue.minOdds) }}</span>
          </div>
          <div class="range-row">
            <span>Max</span>
            <input
              type="range"
              min="-200"
              max="2000"
              step="50"
              :value="modelValue.maxOdds"
              @input="updateSetting('maxOdds', parseInt($event.target.value))"
            />
            <span class="range-value">{{ formatOdds(modelValue.maxOdds) }}</span>
          </div>
        </div>
      </div>

      <!-- Exclude Player Props -->
      <div class="setting-group">
        <label class="checkbox-item">
          <input
            type="checkbox"
            :checked="modelValue.excludePlayerProps"
            @change="updateSetting('excludePlayerProps', $event.target.checked)"
          />
          <span>Exclude Player Props</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      betStyle: 'Parlay',
      minLegs: 2,
      maxLegs: 4,
      minOdds: -150,
      maxOdds: 500,
      excludePlayerProps: false,
      riskLevel: 'average',
      recommendationCount: 3,
      promptMode: 'standard',
      outputFormat: 'markdown',
      requireCitations: true,
      lookbackGames: 10,
      injuryFreshnessHours: 24
    })
  }
})

const emit = defineEmits(['update:modelValue'])

function updateSetting(key, value) {
  let newValue = { ...props.modelValue, [key]: value }

  // Ensure min doesn't exceed max
  if (key === 'minLegs' && value > newValue.maxLegs) newValue.maxLegs = value
  if (key === 'maxLegs' && value < newValue.minLegs) newValue.minLegs = value
  if (key === 'minOdds' && value > newValue.maxOdds) newValue.maxOdds = value
  if (key === 'maxOdds' && value < newValue.minOdds) newValue.minOdds = value

  emit('update:modelValue', newValue)
}

function formatOdds(odds) {
  return odds >= 0 ? `+${odds}` : `${odds}`
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

.selector-body {
  padding: 12px 16px;
}

.setting-group {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}

.setting-group:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.setting-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
  font-weight: 500;
}

.setting-hint {
  margin-top: 8px;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  line-height: 1.3;
}

.radio-group {
  display: flex;
  gap: 16px;
}

.radio-group.vertical {
  flex-direction: row;
  flex-wrap: wrap;
  gap: 12px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 0.8125rem;
  color: var(--text-primary);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
}

.radio-item:hover {
  background: var(--bg-tertiary);
}

.radio-item input {
  accent-color: var(--accent);
}

.range-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.range-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.range-row span:first-child {
  width: 30px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.range-row input[type="range"] {
  flex: 1;
  accent-color: var(--accent);
}

.range-value {
  width: 50px;
  text-align: right;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--accent);
}

.range-row.single {
  display: flex;
  align-items: center;
  gap: 10px;
}

.range-row.single input[type="range"] {
  flex: 1;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 0.8125rem;
  color: var(--text-primary);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
}

.checkbox-item:hover {
  background: var(--bg-tertiary);
}

.checkbox-item input {
  accent-color: var(--accent);
}
</style>
