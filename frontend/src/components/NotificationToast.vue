<template>
  <div class="toast-container">
    <TransitionGroup name="toast">
      <div v-for="t in toasts" :key="t.id" class="toast" :class="t.type" @click="dismiss(t.id)">
        <span class="toast-icon">{{ iconFor(t.type) }}</span>
        <div class="toast-content">
          <div class="toast-title">{{ t.title }}</div>
          <div class="toast-msg" v-if="t.message">{{ t.message }}</div>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

export interface Toast { id: string; type: 'idea' | 'violation' | 'info' | 'error'; title: string; message?: string }

const toasts = ref<Toast[]>([])

function iconFor(type: Toast['type']) {
  return { idea: '💡', violation: '⚠️', info: '🐾', error: '🙀' }[type]
}

function show(t: Omit<Toast, 'id'>, duration = 5000) {
  const id = crypto.randomUUID()
  toasts.value.push({ id, ...t })
  setTimeout(() => dismiss(id), duration)
}

function dismiss(id: string) {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

defineExpose({ show, dismiss })
</script>

<style scoped>
.toast-container { position: fixed; bottom: 1.5rem; right: 1.5rem; z-index: 9999; display: flex; flex-direction: column; gap: 0.5rem; pointer-events: none; }
.toast {
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--radius-lg); padding: 0.75rem 1rem;
  display: flex; gap: 0.6rem; align-items: flex-start;
  cursor: pointer; pointer-events: all; max-width: 300px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}
.toast.idea     { border-left: 3px solid #a78bfa; }
.toast.violation { border-left: 3px solid #f59e0b; }
.toast.error    { border-left: 3px solid #f87171; }
.toast.info     { border-left: 3px solid var(--color-green); }
.toast-icon { font-size: 1.1rem; flex-shrink: 0; }
.toast-title { font-weight: 600; font-size: 0.875rem; }
.toast-msg { font-size: 0.8rem; color: var(--color-text-dim); margin-top: 0.15rem; }
.toast-enter-active, .toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from { opacity: 0; transform: translateY(10px); }
.toast-leave-to   { opacity: 0; transform: translateY(10px); }
</style>
