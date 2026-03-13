<template>
  <div class="teamview">
    <h2>🐱 Teams</h2>
    <div v-if="loading" class="dim">Loading…</div>
    <div v-else class="teams">
      <div v-for="team in teams" :key="team.id" class="team-card">
        <div class="team-header">
          <span class="team-name">{{ team.name }}</span>
          <span class="team-id dim">#{{ team.id.slice(0, 8) }}</span>
        </div>
        <div class="leader-row" v-if="team.leader">
          <AvatarDisplay :name="team.leader" :size="28" />
          <span class="leader-label">{{ team.leader }}</span>
          <span class="leader-badge">leader</span>
        </div>
        <div class="progress">
          <div class="progress-labels">
            <span class="dim">Tasks</span>
            <span>{{ team.done_count }}/{{ team.task_count }}</span>
          </div>
          <div class="bar-wrap">
            <div class="bar" :style="{ width: pct(team) + '%' }" />
          </div>
        </div>
        <div class="agents-row" v-if="team.agents?.length">
          <AvatarDisplay v-for="a in team.agents" :key="a" :name="a" :size="22" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AvatarDisplay from '../components/AvatarDisplay.vue'

interface Team { id: string; name: string; leader?: string; agents: string[]; task_count: number; done_count: number }

const teams = ref<Team[]>([])
const loading = ref(true)

function pct(t: Team) { return t.task_count ? Math.round((t.done_count / t.task_count) * 100) : 0 }

onMounted(async () => {
  try {
    const res = await fetch('/api/v2/teams')
    if (res.ok) teams.value = await res.json()
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.teamview { padding: 1.5rem; overflow-y: auto; height: 100%; }
h2 { color: var(--color-amber); font-size: 1.1rem; margin-bottom: 1.25rem; }
.teams { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1rem; }
.team-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
.team-header { display: flex; align-items: center; justify-content: space-between; }
.team-name { font-weight: 600; font-size: 0.95rem; }
.leader-row { display: flex; align-items: center; gap: 0.5rem; }
.leader-label { font-size: 0.875rem; flex: 1; }
.leader-badge { background: var(--color-amber); color: var(--color-bg); border-radius: 99px; padding: 0.1rem 0.5rem; font-size: 0.68rem; font-weight: 700; }
.progress-labels { display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 0.3rem; }
.bar-wrap { background: var(--color-surface-2); border-radius: 99px; height: 6px; }
.bar { height: 100%; background: var(--color-green); border-radius: 99px; transition: width 0.4s; }
.agents-row { display: flex; gap: 0.25rem; flex-wrap: wrap; }
.dim { color: var(--color-text-dim); font-size: 0.78rem; }
</style>
