<template>
  <div class="gallery">
    <div class="gallery-header">
      <h2>🐾 Agents</h2>
      <input v-model="search" placeholder="Search agents…" class="search" />
    </div>
    <div v-if="loading" class="loading">Loading agents…</div>
    <div v-else class="grid">
      <div v-for="agent in filtered" :key="agent.name" class="card"
        @click="$router.push(`/agents/${agent.name}`)">
        <AvatarDisplay :avatar-svg="(agent as any).avatar_svg" :name="agent.name" :size="56" />
        <div class="card-info">
          <div class="card-name">{{ agent.name }}</div>
          <div class="card-role">{{ agent.role }}</div>
          <div class="card-team" v-if="agent.team">{{ agent.team }}</div>
        </div>
        <span class="status-dot" :class="agent.status" />
      </div>
    </div>
    <div v-if="!loading && filtered.length === 0" class="empty">No agents found 🙀</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/client'
import AvatarDisplay from '../components/AvatarDisplay.vue'
import type { Agent } from '../types'

const agents = ref<Agent[]>([])
const loading = ref(true)
const search = ref('')

const filtered = computed(() =>
  agents.value.filter(a =>
    a.name.toLowerCase().includes(search.value.toLowerCase()) ||
    a.role.toLowerCase().includes(search.value.toLowerCase())
  )
)

onMounted(async () => {
  const res = await api.getAgents()
  if (res.ok) agents.value = res.data
  loading.value = false
})
</script>

<style scoped>
.gallery { padding: 1.5rem; overflow-y: auto; height: 100%; }
.gallery-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; }
h2 { color: var(--color-amber); font-size: 1.1rem; }
.search { max-width: 200px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 1rem; }
.card {
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--radius-lg); padding: 1rem; cursor: pointer;
  display: flex; flex-direction: column; align-items: center; gap: 0.5rem;
  position: relative; transition: border-color 0.15s;
}
.card:hover { border-color: var(--color-amber); }
.card-name { font-weight: 600; font-size: 0.9rem; text-align: center; }
.card-role { font-size: 0.75rem; color: var(--color-text-dim); text-align: center; }
.card-team { font-size: 0.7rem; color: var(--color-amber-dim); text-align: center; }
.status-dot { position: absolute; top: 0.6rem; right: 0.6rem; width: 8px; height: 8px; border-radius: 50%; }
.status-dot.online { background: var(--color-green); }
.status-dot.idle   { background: var(--color-amber); }
.status-dot.offline { background: var(--color-text-dim); }
.loading, .empty { color: var(--color-text-dim); padding: 2rem; }
</style>
