import { ref } from 'vue'

const apiUsage = ref({ requestsUsed: null, requestsRemaining: null })

export function useOddsApi() {
  const loading = ref(false)
  const error = ref(null)

  async function fetchGames(sportKey, bookmakers, markets) {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      if (bookmakers.length) params.append('bookmakers', bookmakers.join(','))
      if (markets.length) params.append('markets', markets.join(','))

      const response = await fetch(`/api/games/${sportKey}?${params}`)
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Failed to fetch games')
      }

      const data = await response.json()
      if (data.usage) {
        apiUsage.value = data.usage
      }
      return data.games
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Generate prompt (payload shape matches backend/routes/api.js)
   */
  async function generatePrompt(games, sportsbooks, betTypes, parlaySettings) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/generate-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          games,
          sportsbooks,
          betTypes,
          parlaySettings
        })
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Failed to generate prompt')
      }

      const data = await response.json()
      return data.prompt
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function validateApiKey() {
    try {
      const response = await fetch('/api/validate-key')
      const data = await response.json()
      return data.valid
    } catch {
      return false
    }
  }

  async function clearCache() {
    try {
      await fetch('/api/clear-cache', { method: 'POST' })
    } catch (err) {
      console.error('Failed to clear cache:', err)
    }
  }

  return {
    loading,
    error,
    apiUsage,
    fetchGames,
    generatePrompt,
    validateApiKey,
    clearCache
  }
}
