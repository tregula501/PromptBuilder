<template>
  <div id="app">
    <header class="app-header">
      <div class="header-left">
        <h1>Betting Prompt Builder</h1>
      </div>
      <div class="header-right">
        <div v-if="apiUsage?.requestsRemaining !== null && apiUsage?.requestsRemaining !== undefined" class="api-usage">
          API remaining: <strong>{{ apiUsage.requestsRemaining }}</strong>
        </div>
        <div class="shortcuts" title="Keyboard shortcuts">
          Ctrl+Enter: Generate · Ctrl+C: Copy Prompt
        </div>
        <button @click="copyShareLink" class="secondary-btn">
          {{ shareCopied ? 'Link Copied' : 'Copy Share Link' }}
        </button>
      </div>
    </header>

    <main class="app-main">
      <section class="wizard">
        <WizardStepper
          :steps="wizardSteps"
          :current-step="currentStep"
          :completed-steps="completedSteps"
          :unlocked-steps="unlockedSteps"
          @go="goToStep"
        />

        <div class="wizard-step">
          <h2 ref="stepHeadingEl" tabindex="-1" class="step-title">
            {{ wizardSteps[currentStep - 1]?.title }}
          </h2>
          <p class="step-subtitle">
            {{ wizardSteps[currentStep - 1]?.subtitle }}
          </p>

          <!-- Step 1: Configure -->
          <div v-if="currentStep === 1" class="step-body">
            <div class="card-grid">
              <div class="card">
                <SportSelector v-model="selectedSports" />
              </div>
              <div class="card">
                <SportsbookSelector v-model="selectedSportsbooks" />
              </div>
              <div class="card">
                <BetTypeSelector v-model="selectedBetTypes" :selected-sports="selectedSports" />
              </div>
            </div>

            <div class="helper-row">
              <div class="helper">
                <strong>Tip:</strong> After picking sports/books/types, fetch games to populate the list. Manual-only sports can be entered as matchups in the next step.
              </div>
            </div>
          </div>

          <!-- Step 2: Games -->
          <div v-else-if="currentStep === 2" class="step-body">
            <GameSelector
              v-model="selectedGames"
              :games="games"
              :loading="gamesLoading"
              :error="gamesError"
              :fetch-loading="gamesLoading"
              :can-fetch="canFetchGames"
              :selected-sports="selectedSports"
              @retry="fetchGames"
              @fetch="fetchGames"
              @add-manual-game="addManualGame"
            />
          </div>

          <!-- Step 3: Settings -->
          <div v-else-if="currentStep === 3" class="step-body">
            <PresetManager :current-state="currentPresetState" @apply="applyPreset" />
            <ParlaySettings v-model="parlaySettings" />
          </div>

          <!-- Step 4: Output -->
          <div v-else class="step-body">
            <PromptOutput
              :prompt="generatedPrompt"
              :loading="promptLoading"
              :error="promptError"
            />
          </div>
        </div>

        <div class="wizard-footer">
          <div v-if="primaryDisabledReason" class="disabled-reason">
            {{ primaryDisabledReason }}
          </div>

          <div class="footer-actions">
            <button v-if="currentStep > 1" class="secondary-btn" @click="backStep" :disabled="promptLoading || gamesLoading">
              Back
            </button>

            <button
              v-if="currentStep === 1"
              class="generate-btn"
              @click="fetchGamesAndAdvance"
              :disabled="!canStart || gamesLoading"
            >
              {{ gamesLoading ? 'Loading…' : 'Fetch Games' }}
            </button>

            <button
              v-else-if="currentStep === 2"
              class="generate-btn"
              @click="nextStep"
              :disabled="selectedGames.length === 0"
            >
              Continue to Settings
            </button>

            <button
              v-else-if="currentStep === 3"
              class="generate-btn"
              @click="generatePrompt"
              :disabled="!canGenerate || promptLoading"
            >
              {{ promptLoading ? 'Generating…' : 'Generate Prompt' }}
            </button>

            <button
              v-else
              class="generate-btn"
              @click="goToStep(3)"
              :disabled="promptLoading"
            >
              Back to Settings
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import SportSelector from './components/SportSelector.vue'
import SportsbookSelector from './components/SportsbookSelector.vue'
import BetTypeSelector from './components/BetTypeSelector.vue'
import GameSelector from './components/GameSelector.vue'
import ParlaySettings from './components/ParlaySettings.vue'
import PromptOutput from './components/PromptOutput.vue'
import WizardStepper from './components/WizardStepper.vue'
import PresetManager from './components/PresetManager.vue'
import { useOddsApi } from './composables/useOddsApi'
import { sportsbooks as sportsbooksCatalog } from './data/sportsbooks'
import { getSportByKey, isManualOnlySport } from './data/sports.js'

const selectedSports = ref([])
const selectedSportsbooks = ref(['fanduel', 'draftkings', 'betmgm'])
const selectedBetTypes = ref(['h2h', 'spreads', 'totals'])
const selectedGames = ref([])
const parlaySettings = ref({
  betStyle: 'Parlay',
  minLegs: 2,
  maxLegs: 4,
  minOdds: -150,
  maxOdds: 500,
  excludePlayerProps: false,
  riskLevel: 'average',
  recommendationCount: 3,
  promptMode: 'standard', // 'standard' | 'compact'
  outputFormat: 'markdown', // 'markdown' | 'json'
  requireCitations: true,
  lookbackGames: 10,
  injuryFreshnessHours: 24
})

const fetchedGames = ref([])
const manualGames = ref([])
let manualGameSeq = 0

const games = computed(() => {
  return [...manualGames.value, ...fetchedGames.value]
})
const gamesLoading = ref(false)
const gamesError = ref(null)

const generatedPrompt = ref('')
const promptLoading = ref(false)
const promptError = ref(null)

const { apiUsage, fetchGames: fetchGamesForSport, generatePrompt: generatePromptApi } = useOddsApi()

const currentStep = ref(1)
const stepHeadingEl = ref(null)
const shareCopied = ref(false)

const wizardSteps = [
  { id: 1, title: 'Configure', subtitle: 'Pick sports, sportsbooks, and bet types.' },
  { id: 2, title: 'Games', subtitle: 'Fetch/select games or add manual matchups.' },
  { id: 3, title: 'Settings', subtitle: 'Tune prompt format, risk, odds, and research windows.' },
  { id: 4, title: 'Output', subtitle: 'Copy and share the generated prompt.' }
]

const canGenerate = computed(() => {
  return selectedGames.value.length > 0 &&
         selectedSportsbooks.value.length > 0 &&
         selectedBetTypes.value.length > 0
})

const canStart = computed(() => {
  return selectedSports.value.length > 0 &&
    selectedSportsbooks.value.length > 0 &&
    selectedBetTypes.value.length > 0
})

const apiBookmakers = computed(() => {
  const apiAvailable = new Set(sportsbooksCatalog.filter(b => b.availableInApi).map(b => b.key))
  return selectedSportsbooks.value.filter(k => apiAvailable.has(k))
})

const apiMarkets = computed(() => {
  // The Odds API markets we currently support fetching efficiently.
  // Note: player props are supported in the prompt via “research if missing” until a per-sport market map is added.
  const supported = new Set(['h2h', 'spreads', 'totals'])
  return selectedBetTypes.value.filter(k => supported.has(k))
})

const selectedApiSports = computed(() => {
  return selectedSports.value.filter(sportKey => !isManualOnlySport(sportKey))
})

const canFetchGames = computed(() => {
  return selectedSports.value.length > 0 && selectedApiSports.value.length > 0
})

const currentPresetState = computed(() => ({
  sports: selectedSports.value,
  books: selectedSportsbooks.value,
  types: selectedBetTypes.value,
  settings: parlaySettings.value
}))

function applyPreset(state) {
  if (!state || typeof state !== 'object') return
  if (Array.isArray(state.sports)) selectedSports.value = [...state.sports]
  if (Array.isArray(state.books)) selectedSportsbooks.value = [...state.books]
  if (Array.isArray(state.types)) selectedBetTypes.value = [...state.types]
  if (state.settings && typeof state.settings === 'object') {
    parlaySettings.value = { ...parlaySettings.value, ...state.settings }
  }
}

const completedSteps = computed(() => {
  const out = []
  if (canStart.value) out.push(1)
  if (selectedGames.value.length > 0) out.push(2)
  if (selectedGames.value.length > 0) out.push(3)
  if (generatedPrompt.value) out.push(4)
  return out
})

const unlockedSteps = computed(() => {
  const out = [1]
  if (canStart.value) out.push(2)
  if (selectedGames.value.length > 0) out.push(3)
  if (generatedPrompt.value || promptLoading.value) out.push(4)
  return out
})

const primaryDisabledReason = computed(() => {
  if (currentStep.value === 1 && !canStart.value) return 'Select at least one sport, sportsbook, and bet type to continue.'
  if (currentStep.value === 2 && selectedGames.value.length === 0) return 'Select at least one game (or add a manual matchup) to continue.'
  if (currentStep.value === 3 && !canGenerate.value) return 'Select games, sportsbooks, and bet types before generating.'
  return ''
})

async function fetchGames() {
  if (!selectedSports.value.length) return

  gamesLoading.value = true
  gamesError.value = null
  fetchedGames.value = []
  // Preserve manually-added matchups across refreshes
  selectedGames.value = selectedGames.value.filter(g => g?.source === 'manual')

  try {
    // Fetch all selected sports in parallel.
    const sportsToFetch = selectedSports.value.filter(sportKey => !isManualOnlySport(sportKey))

    // If everything selected is manual-only, nothing to fetch. User can add games manually.
    if (!sportsToFetch.length) {
      fetchedGames.value = []
      return
    }

    const results = await Promise.allSettled(
      sportsToFetch.map(sportKey =>
        fetchGamesForSport(sportKey, apiBookmakers.value, apiMarkets.value)
      )
    )

    const allGames = []
    const errors = []
    for (let i = 0; i < results.length; i++) {
      const result = results[i]
      if (result.status === 'fulfilled') {
        allGames.push(...(result.value || []))
      } else {
        errors.push(`${sportsToFetch[i]}: ${result.reason?.message || 'failed'}`)
      }
    }

    fetchedGames.value = allGames
    if (!allGames.length && errors.length) {
      gamesError.value = errors.join(' | ')
    }
  } catch (err) {
    gamesError.value = err.message
  } finally {
    gamesLoading.value = false
  }
}

function addManualGame({ sportKey, homeTeam, awayTeam, commenceTime }) {
  const sport = getSportByKey(sportKey)
  const game = {
    id: `manual_${Date.now()}_${manualGameSeq++}`,
    sportKey,
    sportTitle: sport?.title || sportKey,
    commenceTime: commenceTime || null,
    homeTeam,
    awayTeam,
    bookmakers: [],
    source: 'manual'
  }

  manualGames.value = [game, ...manualGames.value]
  selectedGames.value = [...selectedGames.value, game]
}

async function generatePrompt() {
  if (!canGenerate.value) return

  promptLoading.value = true
  promptError.value = null

  try {
    generatedPrompt.value = await generatePromptApi(
      selectedGames.value,
      selectedSportsbooks.value,
      selectedBetTypes.value,
      parlaySettings.value
    )
    currentStep.value = 4
    await nextTick()
    stepHeadingEl.value?.focus?.()
  } catch (err) {
    promptError.value = err.message
  } finally {
    promptLoading.value = false
  }
}

// Keyboard shortcuts
function handleKeydown(e) {
  // Ctrl+Enter to generate prompt
  if (e.ctrlKey && e.key === 'Enter' && canGenerate.value && !promptLoading.value) {
    generatePrompt()
  }
}

function goToStep(step) {
  // Only allow jumping forward when previous steps are satisfied
  if (step === 2 && !canStart.value) return
  if (step === 3 && selectedGames.value.length === 0) return
  if (step === 4 && !generatedPrompt.value && !promptLoading.value) return

  currentStep.value = step
  nextTick(() => stepHeadingEl.value?.focus?.())
}

function nextStep() {
  if (currentStep.value === 1) {
    if (!canStart.value) return
    currentStep.value = 2
  } else if (currentStep.value === 2) {
    if (selectedGames.value.length === 0) return
    currentStep.value = 3
  } else if (currentStep.value === 3) {
    // step 3 primary action is generate
    return
  } else {
    return
  }
  nextTick(() => stepHeadingEl.value?.focus?.())
}

function backStep() {
  if (currentStep.value <= 1) return
  currentStep.value = Math.max(1, currentStep.value - 1)
  nextTick(() => stepHeadingEl.value?.focus?.())
}

async function fetchGamesAndAdvance() {
  if (!canStart.value) return
  if (canFetchGames.value) {
    await fetchGames()
  }
  currentStep.value = 2
  await nextTick()
  stepHeadingEl.value?.focus?.()
}

onMounted(() => {
  // Restore settings (share-link overrides localStorage)
  try {
    const url = new URL(window.location.href)
    const shared = url.searchParams.get('state')
    const restored = shared ? decodeState(shared) : null

    if (restored) {
      if (Array.isArray(restored?.sports)) selectedSports.value = restored.sports
      if (Array.isArray(restored?.books)) selectedSportsbooks.value = restored.books
      if (Array.isArray(restored?.types)) selectedBetTypes.value = restored.types
      if (restored?.settings && typeof restored.settings === 'object') {
        parlaySettings.value = { ...parlaySettings.value, ...restored.settings }
      }
    } else {
      const saved = localStorage.getItem('betting-prompt-settings')
      if (saved) {
        const state = JSON.parse(saved)
        if (Array.isArray(state?.sports)) selectedSports.value = state.sports
        if (Array.isArray(state?.books)) selectedSportsbooks.value = state.books
        if (Array.isArray(state?.types)) selectedBetTypes.value = state.types
        if (state?.settings && typeof state.settings === 'object') {
          parlaySettings.value = { ...parlaySettings.value, ...state.settings }
        }
      }
    }
  } catch (err) {
    console.warn('Failed to restore settings:', err)
  }

  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// Persist settings (not games, to avoid large localStorage payloads)
watch(
  [selectedSports, selectedSportsbooks, selectedBetTypes, parlaySettings],
  ([sports, books, types, settings]) => {
    try {
      localStorage.setItem('betting-prompt-settings', JSON.stringify({
        sports,
        books,
        types,
        settings,
        timestamp: Date.now()
      }))
    } catch (err) {
      console.warn('Failed to save settings:', err)
    }
  },
  { deep: true }
)

function buildShareUrl() {
  const url = new URL(window.location.href)
  url.searchParams.set('state', encodeState({
    sports: selectedSports.value,
    books: selectedSportsbooks.value,
    types: selectedBetTypes.value,
    settings: parlaySettings.value
  }))
  return url.toString()
}

async function copyShareLink() {
  const url = buildShareUrl()
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(url)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = url
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    shareCopied.value = true
    window.setTimeout(() => { shareCopied.value = false }, 1500)
  } catch (err) {
    console.error('Failed to copy share link:', err)
  }
}

function encodeState(obj) {
  return btoa(unescape(encodeURIComponent(JSON.stringify(obj))))
}

function decodeState(encoded) {
  try {
    const json = decodeURIComponent(escape(atob(encoded)))
    return JSON.parse(json)
  } catch {
    return null
  }
}
</script>

<style>
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16162a;
  --bg-tertiary: #252542;
  --border-light: #2d2d4a;
  --border-medium: #3d3d5c;
  --text-primary: #e8e8ef;
  --text-secondary: #9090a8;
  --text-tertiary: #6b6b82;
  --accent: #14b8a6;
  --accent-light: #2dd4bf;
  --accent-bg: rgba(20, 184, 166, 0.1);
  --error: #f87171;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.4);
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-secondary);
  color: var(--text-primary);
  height: 100vh;
  overflow: hidden;
  font-size: 14px;
  line-height: 1.5;
}

#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.api-usage {
  font-size: 0.75rem;
  color: var(--text-secondary);
  padding: 6px 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: rgba(255,255,255,0.02);
}

.api-usage strong {
  color: var(--text-primary);
  font-weight: 600;
}

.shortcuts {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  padding: 6px 10px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: rgba(255,255,255,0.02);
}

.app-header h1 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.app-main {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
  justify-content: center;
}

.wizard {
  width: min(1100px, 100%);
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  overflow: hidden;
}

.wizard-step {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.step-title {
  padding: 16px 20px 6px;
  font-size: 1rem;
  font-weight: 650;
  outline: none;
}

.step-subtitle {
  padding: 0 20px 14px;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.step-body {
  padding: 0 20px 20px;
  overflow: auto;
  min-height: 0;
}

.card-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}

.card {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: rgba(255,255,255,0.01);
}

.helper-row {
  margin-top: 14px;
}

.helper {
  font-size: 0.85rem;
  color: var(--text-secondary);
  padding: 12px 14px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: rgba(20, 184, 166, 0.06);
}

.wizard-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 4px 0;
}

.disabled-reason {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.footer-actions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

.generate-btn {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.generate-btn:hover:not(:disabled) {
  background: var(--accent-light);
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.secondary-btn {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.secondary-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

@media (max-width: 1200px) {
  .card-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .wizard {
    padding: 14px 14px 18px;
  }
}
</style>
