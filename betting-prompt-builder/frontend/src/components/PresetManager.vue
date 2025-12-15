<template>
  <div class="presets">
    <div class="presets-header">
      <h3>Presets</h3>
      <span class="hint">Save/load your configuration + settings</span>
    </div>

    <div class="presets-body">
      <div class="row">
        <select v-model="selectedId" class="select" aria-label="Preset">
          <option value="">Select a preset…</option>
          <option v-for="p in presets" :key="p.id" :value="p.id">
            {{ p.name }}
          </option>
        </select>

        <button class="secondary-btn" type="button" @click="loadSelected" :disabled="!selectedId">
          Load
        </button>
        <button class="secondary-btn" type="button" @click="saveNew" :disabled="!canSave">
          Save New
        </button>
      </div>

      <div class="row">
        <input v-model="nameDraft" class="input" type="text" placeholder="Preset name…" />

        <button class="secondary-btn" type="button" @click="updateSelected" :disabled="!selectedId || !canSave">
          Update
        </button>
        <button class="danger-btn" type="button" @click="deleteSelected" :disabled="!selectedId">
          Delete
        </button>
      </div>

      <div v-if="message" class="message" :class="{ ok: messageKind === 'ok', error: messageKind === 'error' }">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

const STORAGE_KEY = 'betting-prompt-presets'

const props = defineProps({
  currentState: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['apply'])

const presets = ref([])
const selectedId = ref('')
const nameDraft = ref('')
const message = ref('')
const messageKind = ref('ok') // 'ok' | 'error'

const canSave = computed(() => {
  const s = props.currentState || {}
  return Array.isArray(s.sports) && Array.isArray(s.books) && Array.isArray(s.types) && typeof s.settings === 'object'
})

function setMessage(text, kind = 'ok') {
  message.value = text
  messageKind.value = kind
  window.setTimeout(() => {
    if (message.value === text) message.value = ''
  }, 2000)
}

function loadPresets() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    presets.value = Array.isArray(parsed) ? parsed : []
  } catch {
    presets.value = []
  }
}

function persistPresets() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(presets.value))
}

function getSelectedPreset() {
  return presets.value.find(p => p.id === selectedId.value) || null
}

function loadSelected() {
  const p = getSelectedPreset()
  if (!p) return
  emit('apply', p.state)
  setMessage(`Loaded: ${p.name}`, 'ok')
}

function saveNew() {
  if (!canSave.value) return
  const name = (nameDraft.value || '').trim() || `Preset ${presets.value.length + 1}`
  const now = Date.now()
  const id = `preset_${now}_${Math.random().toString(16).slice(2)}`

  const preset = {
    id,
    name,
    createdAt: now,
    updatedAt: now,
    state: props.currentState
  }

  presets.value = [preset, ...presets.value]
  persistPresets()
  selectedId.value = id
  setMessage('Preset saved', 'ok')
}

function updateSelected() {
  if (!canSave.value) return
  const idx = presets.value.findIndex(p => p.id === selectedId.value)
  if (idx < 0) return

  const existing = presets.value[idx]
  const name = (nameDraft.value || '').trim() || existing.name
  presets.value.splice(idx, 1, {
    ...existing,
    name,
    updatedAt: Date.now(),
    state: props.currentState
  })
  persistPresets()
  setMessage('Preset updated', 'ok')
}

function deleteSelected() {
  const p = getSelectedPreset()
  if (!p) return
  const ok = window.confirm(`Delete preset "${p.name}"?`)
  if (!ok) return

  presets.value = presets.value.filter(x => x.id !== p.id)
  persistPresets()
  selectedId.value = ''
  setMessage('Preset deleted', 'ok')
}

onMounted(() => {
  loadPresets()
})
</script>

<style scoped>
.presets {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  background: rgba(255,255,255,0.01);
  overflow: hidden;
  margin-bottom: 16px;
}

.presets-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.presets-header h3 {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
}

.hint {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.presets-body {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.select,
.input {
  flex: 1;
  min-width: 220px;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  padding: 8px 10px;
  font-size: 0.85rem;
}

.danger-btn {
  background: transparent;
  color: var(--error);
  border: 1px solid rgba(248, 113, 113, 0.6);
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.danger-btn:hover:not(:disabled) {
  background: rgba(248, 113, 113, 0.12);
}

.danger-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.message.ok {
  color: #34d399;
}

.message.error {
  color: var(--error);
}
</style>


