<template>
  <div class="prompt-output">
    <div class="output-header">
      <h3>Generated Prompt</h3>
      <div class="header-actions">
        <button v-if="prompt" @click="copyToClipboard" class="copy-btn" :class="{ success: copied }">
          {{ copied ? 'Copied!' : 'Copy' }}
        </button>
      </div>
    </div>

    <div class="output-body">
      <div v-if="loading" class="state-message">
        <div class="spinner"></div>
        <span>Generating your prompt...</span>
      </div>

      <div v-else-if="error" class="state-message error">
        <span>{{ error }}</span>
      </div>

      <div v-else-if="!prompt" class="state-message">
        <span>Ready to generate</span>
        <small>Select games and click "Generate" to create your AI betting analysis prompt</small>
      </div>

      <div v-else class="prompt-content">
        <pre>{{ prompt }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  prompt: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null }
})

const copied = ref(false)

async function copyToClipboard() {
  try {
    // Try modern clipboard API first
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(props.prompt)
    } else {
      // Fallback for non-secure contexts (HTTP)
      const textarea = document.createElement('textarea')
      textarea.value = props.prompt
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

// Keyboard shortcut: Ctrl+C to copy prompt
function handleKeydown(e) {
  if (e.ctrlKey && e.key === 'c' && props.prompt && !window.getSelection()?.toString()) {
    e.preventDefault()
    copyToClipboard()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.prompt-output {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
}

.output-header h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.copy-btn {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}

.copy-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.copy-btn.success {
  color: #34d399;
  border-color: #34d399;
  background: rgba(52, 211, 153, 0.1);
}

.output-body {
  flex: 1;
  overflow: hidden;
  padding: 16px;
  min-height: 0;
  display: flex;
  flex-direction: column;
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

.prompt-content {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 16px;
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--text-primary);
}
</style>
