<template>
  <div class="history">
    <h3>📋 Contributions</h3>
    <div v-if="loading" class="dim">Loading…</div>
    <div v-else-if="items.length === 0" class="dim">No contributions yet 🐾</div>
    <div v-else class="timeline">
      <div v-for="item in items" :key="item.id" class="entry">
        <span class="dot" :class="item.type" />
        <div class="content">
          <span class="label">{{ item.label }}</span>
          <span class="ts">{{ fmtDate(item.created_at) }}</span>
          <div class="desc" v-if="item.description">{{ item.description }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface ContribItem { id: string; type: 'task'|'chat'|'idea'; label: string; description?: string; created_at: string }

const props = defineProps<{ agentName: string }>()
const items = ref<ContribItem[]>([])
const loading = ref(true)

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  try {
    const res = await fetch(`/api/v2/agents/${props.agentName}/contributions`)
    if (res.ok) items.value = await res.json()
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.history { margin-top: 1rem; }
h3 { color: var(--color-amber); font-size: 0.95rem; margin-bottom: 0.75rem; }
.dim { color: var(--color-text-dim); font-size: 0.875rem; }
.timeline { display: flex; flex-direction: column; gap: 0.6rem; }
.entry { display: flex; gap: 0.75rem; align-items: flex-start; }
.dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 0.3rem; }
.dot.task { background: var(--color-amber); }
.dot.chat { background: var(--color-green); }
.dot.idea { background: #a78bfa; }
.content { flex: 1; }
.label { font-size: 0.875rem; font-weight: 500; }
.ts { font-size: 0.72rem; color: var(--color-text-dim); margin-left: 0.5rem; }
.desc { font-size: 0.8rem; color: var(--color-text-dim); margin-top: 0.2rem; }
</style>
