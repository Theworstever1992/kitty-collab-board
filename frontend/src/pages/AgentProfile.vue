<template>
  <div class="profile" v-if="agent">
    <div class="profile-header">
      <AvatarDisplay :avatar-svg="(agent as any).avatar_svg" :name="agent.name" :size="80" />
      <div class="profile-meta">
        <h2>{{ agent.name }} <span class="status-dot" :class="agent.status" /></h2>
        <div class="role">{{ agent.role }}<span v-if="agent.team"> · {{ agent.team }}</span></div>
        <div class="bio" v-if="(agent as any).bio">{{ (agent as any).bio }}</div>
        <div class="skills" v-if="(agent as any).skills?.length">
          <span v-for="s in (agent as any).skills" :key="s" class="skill-chip">{{ s }}</span>
        </div>
      </div>
      <div class="actions">
        <button class="btn-ghost" @click="editing = !editing">✏️ Edit</button>
        <button class="btn-ghost" @click="exportAgent">⬇️ Export</button>
      </div>
    </div>
    <div v-if="editing" class="edit-section">
      <ProfileEditor :agent="agent" @saved="onSaved" @cancel="editing = false" />
    </div>
    <div class="stats-row">
      <div class="stat">
        <span class="stat-val">{{ budget?.total_cost_usd?.toFixed(4) ?? '—' }}</span>
        <span class="stat-label">USD spent</span>
      </div>
      <div class="stat">
        <span class="stat-val">{{ agent.model }}</span>
        <span class="stat-label">model</span>
      </div>
      <div class="stat">
        <span class="stat-val">{{ agent.status }}</span>
        <span class="stat-label">status</span>
      </div>
    </div>
    <ContributionHistory :agent-name="agent.name" />
  </div>
  <div v-else-if="loading" class="loading">Loading…</div>
  <div v-else class="empty">Agent not found 🙀</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import AvatarDisplay from '../components/AvatarDisplay.vue'
import ProfileEditor from '../components/ProfileEditor.vue'
import ContributionHistory from '../components/ContributionHistory.vue'
import type { Agent, TokenBudget } from '../types'

const route = useRoute()
const agent = ref<Agent | null>(null)
const budget = ref<TokenBudget | null>(null)
const loading = ref(true)
const editing = ref(false)

async function load() {
  const name = route.params.name as string
  const [a, b] = await Promise.all([api.getAgent(name), api.getBudget(name)])
  if (a.ok) agent.value = a.data
  if (b.ok) budget.value = b.data
  loading.value = false
}

async function exportAgent() {
  const name = agent.value?.name; if (!name) return
  const res = await fetch(`/api/v2/agents/${name}/export?format=json`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = `${name}.json`; a.click()
  URL.revokeObjectURL(url)
}

function onSaved(updated: Agent) { agent.value = updated; editing.value = false }
onMounted(load)
</script>

<style scoped>
.profile { padding: 1.5rem; overflow-y: auto; height: 100%; }
.profile-header { display: flex; gap: 1.25rem; align-items: flex-start; margin-bottom: 1.5rem; flex-wrap: wrap; }
.profile-meta { flex: 1; }
h2 { font-size: 1.25rem; display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.status-dot.online { background: var(--color-green); }
.status-dot.idle   { background: var(--color-amber); }
.status-dot.offline { background: var(--color-text-dim); }
.role { color: var(--color-text-dim); font-size: 0.875rem; margin-bottom: 0.5rem; }
.bio { font-size: 0.875rem; line-height: 1.5; margin-bottom: 0.5rem; color: var(--color-cream-dim); }
.skills { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.skill-chip { background: var(--color-surface-2); border: 1px solid var(--color-border); border-radius: 99px; padding: 0.15rem 0.6rem; font-size: 0.72rem; color: var(--color-text-dim); }
.actions { display: flex; flex-direction: column; gap: 0.5rem; }
.stats-row { display: flex; gap: 1.5rem; margin-bottom: 1.5rem; }
.stat { display: flex; flex-direction: column; gap: 0.15rem; }
.stat-val { font-size: 1.1rem; font-weight: 700; color: var(--color-amber); }
.stat-label { font-size: 0.72rem; color: var(--color-text-dim); }
.loading, .empty { padding: 2rem; color: var(--color-text-dim); }
</style>
