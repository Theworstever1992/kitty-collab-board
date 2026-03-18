<template>
  <div class="ctx-panel" :class="{ open: items.length > 0 || loading }">
    <div class="ctx-header">
      <span>🧠 Context</span>
      <span class="ctx-count" v-if="items.length">{{ items.length }}</span>
      <button class="close-btn" @click="$emit('close')" aria-label="Close context panel">✕</button>
    </div>
    <div v-if="loading" class="dim">Retrieving context…</div>
    <div v-else-if="items.length === 0" class="dim">No context injected yet</div>
    <div v-else class="ctx-list">
      <div v-for="item in items" :key="item.id" class="ctx-item">
        <div class="ctx-item-header">
          <span class="ctx-type">{{ item.source_type }}</span>
          <span class="ctx-score">{{ ((item.similarity_score ?? 0) * 100).toFixed(0) }}% match</span>
          <span class="ctx-ts dim">{{ fmtDate(item.created_at) }}</span>
        </div>
        <div class="ctx-text">{{ item.content }}</div>
        <div class="ctx-meta dim" v-if="item.source_id">
          task: {{ item.source_id.slice(0, 8) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { ContextItem } from '../types'

const props = defineProps<{ taskId?: string | null }>()
defineEmits<{ (e: 'close'): void }>()

const items = ref<ContextItem[]>([])
const loading = ref(false)

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

watch(() => props.taskId, async (id) => {
  if (!id) { items.value = []; return }
  loading.value = true
  try {
    const res = await fetch(`/api/v2/context?task_id=${id}&top_k=5`)
    if (res.ok) items.value = await res.json()
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.ctx-panel {
  position: fixed; right: 0; top: 0; bottom: 0; width: 320px;
  background: var(--color-surface); border-left: 1px solid var(--color-border);
  display: flex; flex-direction: column; transform: translateX(100%);
  transition: transform 0.25s; z-index: 100; overflow: hidden;
}
.ctx-panel.open { transform: translateX(0); }
.ctx-header { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; border-bottom: 1px solid var(--color-border); font-weight: 600; font-size: 0.875rem; }
.ctx-count { background: var(--color-amber); color: var(--color-bg); border-radius: 99px; padding: 0.1rem 0.5rem; font-size: 0.72rem; }
.close-btn { margin-left: auto; background: none; border: none; color: var(--color-text-dim); cursor: pointer; font-size: 0.9rem; }
.ctx-list { overflow-y: auto; flex: 1; padding: 0.75rem; display: flex; flex-direction: column; gap: 0.75rem; }
.ctx-item { background: var(--color-surface-2); border: 1px solid var(--color-border); border-radius: var(--radius); padding: 0.75rem; }
.ctx-item-header { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.4rem; flex-wrap: wrap; }
.ctx-type { background: var(--color-amber); color: var(--color-bg); border-radius: 99px; padding: 0.1rem 0.5rem; font-size: 0.68rem; font-weight: 600; text-transform: uppercase; }
.ctx-score { font-size: 0.72rem; color: var(--color-green); font-weight: 600; }
.ctx-ts { font-size: 0.72rem; margin-left: auto; }
.ctx-text { font-size: 0.8rem; line-height: 1.45; color: var(--color-cream-dim); max-height: 80px; overflow: hidden; }
.ctx-meta { font-size: 0.72rem; margin-top: 0.3rem; font-family: monospace; }
.dim { color: var(--color-text-dim); font-size: 0.8rem; padding: 0.75rem; }
</style>
