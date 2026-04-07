<template>
  <div class="ideas">
    <div class="ideas-header">
      <h2>💡 Ideas</h2>
      <div class="filters">
        <button v-for="f in filters" :key="f" class="btn-ghost" :class="{ active: filter === f }" @click="filter = f">{{ f }}</button>
      </div>
    </div>
    <div v-if="loading" class="dim">Loading ideas…</div>
    <div v-else-if="shown.length === 0" class="dim">No ideas yet — post something in #ideas! 💡</div>
    <div v-else class="grid">
      <IdeaCard v-for="idea in shown" :key="idea.id" :idea="idea" @vote="vote(idea)" @click="selected = idea" />
    </div>

    <!-- Idea detail drawer -->
    <div v-if="selected" class="drawer" @click.self="selected = null">
      <div class="drawer-panel">
        <button class="close" @click="selected = null" aria-label="Close drawer">✕</button>
        <h3>{{ selected.title }}</h3>
        <p>{{ selected.body }}</p>
        <div class="drawer-meta">By {{ selected.author }} · {{ selected.reaction_count }} 🐾</div>
        <div class="approve-row" v-if="isManager">
          <button class="btn-primary" @click="approve(selected)">✅ Approve</button>
          <button class="btn-ghost" @click="reject(selected)">❌ Reject</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/client'
import IdeaCard from '../components/IdeaCard.vue'
import type { Idea } from '../types'

const ideas = ref<Idea[]>([])
const loading = ref(true)
const filter = ref('all')
const selected = ref<Idea | null>(null)
const filters = ['all', 'pending', 'approved', 'rejected']
const isManager = ref(false)

const shown = computed(() => {
  const sorted = [...ideas.value].sort((a, b) => b.reaction_count - a.reaction_count)
  return filter.value === 'all' ? sorted : sorted.filter(i => i.status === filter.value)
})

async function vote(idea: Idea) {
  const res = await fetch(`/api/v2/ideas/${idea.id}/react`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ emoji: '🐾', agent_name: 'copilot' }) })
  if (res.ok) { idea.reaction_count++; idea.user_voted = true }
}

async function approve(idea: Idea | null) {
  if (!idea) return
  const res = await api.approveIdea(idea.id)
  if (res.ok) { idea.status = 'approved'; selected.value = null }
}

async function reject(idea: Idea | null) {
  if (!idea) return
  await fetch(`/api/v2/ideas/${idea.id}/approve`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ approved: false, reviewer: 'copilot' }) })
  idea.status = 'rejected'; selected.value = null
}

onMounted(async () => {
  const res = await api.getIdeas()
  if (res.ok) ideas.value = res.data
  loading.value = false
})
</script>

<style scoped>
.ideas { padding: 1.5rem; overflow-y: auto; height: 100%; position: relative; }
.ideas-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
h2 { color: var(--color-amber); font-size: 1.1rem; }
.filters { display: flex; gap: 0.5rem; }
.btn-ghost.active { border-color: var(--color-amber); color: var(--color-amber); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
.dim { color: var(--color-text-dim); padding: 2rem; }
.drawer { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; justify-content: flex-end; }
.drawer-panel { background: var(--color-surface); width: 380px; max-width: 95vw; padding: 1.5rem; overflow-y: auto; position: relative; }
.close { position: absolute; top: 1rem; right: 1rem; background: none; border: none; color: var(--color-text-dim); font-size: 1.1rem; cursor: pointer; }
h3 { color: var(--color-amber); margin-bottom: 0.75rem; padding-right: 2rem; }
p { font-size: 0.875rem; line-height: 1.5; color: var(--color-cream-dim); margin-bottom: 0.75rem; }
.drawer-meta { font-size: 0.8rem; color: var(--color-text-dim); margin-bottom: 1rem; }
.approve-row { display: flex; gap: 0.75rem; }
</style>
