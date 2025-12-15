<template>
  <div id="app">
    <header class="app-header">
      <div class="header-left">
        <button class="hamburger-btn" @click="sidebarOpen = true">
          <span>&#9776;</span>
        </button>
        <h1>Betting Prompt Builder</h1>
      </div>
      <div class="header-right">
        <div v-if="apiUsage?.requestsRemaining !== null && apiUsage?.requestsRemaining !== undefined" class="api-usage">
          API remaining: <strong>{{ apiUsage.requestsRemaining }}</strong>
        </div>
        <button @click="copyShareLink" class="secondary-btn">
          Copy Share Link
        </button>
        <button @click="generatePrompt" :disabled="!canGenerate || promptLoading" class="generate-btn">
          {{ promptLoading ? 'Generating...' : 'Generate Prompt' }}
        </button>
      </div>
    </header>

    <main class="app-main">
      <div
        class="sidebar-backdrop"
        :class="{ visible: sidebarOpen }"
        @click="sidebarOpen = false"
      ></div>
      <aside class="sidebar" :class="{ open: sidebarOpen }">
        <div class="sidebar-header">
          <span>Settings</span>
          <button class="close-btn" @click="sidebarOpen = false">&times;</button>
        </div>
        <SportSelector v-model="selectedSports" />
        <SportsbookSelector v-model="selectedSportsbooks" />
        <BetTypeSelector v-model="selectedBetTypes" :selected-sports="selectedSports" />
        <ParlaySettings v-model="parlaySettings" />
      </aside>

      <section class="content">
        <div class="content-grid">
          <GameSelector
            v-model="selectedGames"
            :games="games"
            :loading="gamesLoading"
            :error="gamesError"
            :fetch-loading="gamesLoading"
            :can-fetch="selectedSports.length > 0"
            :selected-sports="selectedSports"
            @retry="fetchGames"
            @fetch="fetchGames"
            @add-manual-game="addManualGame"
          />
          <PromptOutput
            :prompt="generatedPrompt"
            :loading="promptLoading"
            :error="promptError"
          />
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import SportSelector from './components/SportSelector.vue'
import SportsbookSelector from './components/SportsbookSelector.vue'
import BetTypeSelector from './components/BetTypeSelector.vue'
import GameSelector from './components/GameSelector.vue'
import ParlaySettings from './components/ParlaySettings.vue'
import PromptOutput from './components/PromptOutput.vue'
import { useOddsApi } from './composables/useOddsApi'
import { sportsbooks as sportsbooksCatalog } from './data/sportsbooks'
import { getSportByKey, isManualOnlySport } from './data/sports.js'

const sidebarOpen = ref(false)
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

const canGenerate = computed(() => {
  return selectedGames.value.length > 0 &&
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
}

.sidebar {
  width: 280px;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-light);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1;
  overflow: hidden;
  padding: 24px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-secondary);
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
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

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hamburger-btn {
  display: none;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-primary);
  cursor: pointer;
  padding: 4px 8px;
}

.sidebar-header {
  display: none;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--border-light);
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}

.close-btn:hover {
  color: var(--text-primary);
}

.sidebar-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 90;
  opacity: 0;
  transition: opacity 0.3s;
}

.sidebar-backdrop.visible {
  opacity: 1;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hamburger-btn {
    display: block;
  }

  .sidebar-header {
    display: flex;
  }

  .sidebar-backdrop {
    display: block;
    pointer-events: none;
  }

  .sidebar-backdrop.visible {
    pointer-events: auto;
  }

  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 300px;
    max-width: 85vw;
    z-index: 100;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    border-right: 1px solid var(--border-light);
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .app-main {
    flex-direction: column;
  }

  .content {
    flex: 1;
    min-height: 0;
  }

  .content-grid {
    grid-template-columns: 1fr;
    overflow: auto;
  }
}
</style>
