<template>
  <div class="dashboard">
    <h2>🐾 Dashboard</h2>
    <div class="cards">
      <div class="card" v-for="s in stats" :key="s.label">
        <span class="card-icon">{{ s.icon }}</span>
        <span class="card-val">{{ s.value ?? '…' }}</span>
        <span class="card-label">{{ s.label }}</span>
      </div>
    </div>

    <div class="row">
      <div class="panel">
        <h3>Recent Tasks</h3>
        <div v-if="tasks.length === 0" class="dim">No tasks yet</div>
        <div v-else class="task-list">
          <div v-for="t in tasks" :key="t.id" class="task-entry">
            <span class="task-status" :class="t.status" />
            <span class="task-title">{{ t.title }}</span>
            <span class="task-agent dim">{{ t.assigned_to }}</span>
          </div>
        </div>
      </div>
      <div class="panel">
        <h3>Trending Ideas</h3>
        <div v-if="ideas.length === 0" class="dim">No ideas yet</div>
        <div v-else class="idea-list">
          <div v-for="idea in ideas" :key="idea.id" class="idea-entry">
            <span class="idea-votes">🐾 {{ idea.reaction_count }}</span>
            <span class="idea-title">{{ idea.title }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="panel agents-panel">
      <h3>Agent Health</h3>
      <div class="agent-health-list">
        <div v-for="a in agents" :key="a.name" class="ah-row">
          <AvatarDisplay :name="a.name" :size="24" />
          <span class="ah-name">{{ a.name }}</span>
          <span class="ah-role dim">{{ a.role }}</span>
          <span class="ah-dot" :class="a.status" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api/client'
import AvatarDisplay from '../components/AvatarDisplay.vue'
import type { Task, Agent, Idea } from '../types'

const tasks = ref<Task[]>([])
const agents = ref<Agent[]>([])
const ideas = ref<Idea[]>([])

const stats = ref([
  { icon: '📋', label: 'Tasks', value: null as number | null },
  { icon: '🐱', label: 'Agents', value: null as number | null },
  { icon: '💡', label: 'Ideas', value: null as number | null },
  { icon: '⚠️', label: 'Violations', value: null as number | null },
])

onMounted(async () => {
  const [t, a, i, v] = await Promise.all([
    api.getTasks(), api.getAgents(), api.getIdeas(), api.getViolations()
  ])
  if (t.ok) { tasks.value = t.data.slice(0, 8); stats.value[0].value = t.data.length }
  if (a.ok) { agents.value = a.data; stats.value[1].value = a.data.length }
  if (i.ok) { ideas.value = [...i.data].sort((x, y) => y.reaction_count - x.reaction_count).slice(0, 5); stats.value[2].value = i.data.length }
  if (v.ok) { stats.value[3].value = v.data.length }
})
</script>

<style scoped>
.dashboard { padding: 1.5rem; overflow-y: auto; height: 100%; }
h2 { color: var(--color-amber); font-size: 1.1rem; margin-bottom: 1.25rem; }
h3 { color: var(--color-amber); font-size: 0.9rem; margin-bottom: 0.75rem; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 0.75rem; margin-bottom: 1.25rem; }
.card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 1rem; display: flex; flex-direction: column; align-items: center; gap: 0.2rem; }
.card-icon { font-size: 1.5rem; }
.card-val { font-size: 1.25rem; font-weight: 700; color: var(--color-amber); }
.card-label { font-size: 0.72rem; color: var(--color-text-dim); }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
.panel { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 1rem; }
.agents-panel { margin-top: 0; }
.task-list, .idea-list { display: flex; flex-direction: column; gap: 0.5rem; }
.task-entry, .idea-entry { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; }
.task-status { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.task-status.pending { background: var(--color-text-dim); }
.task-status.in_progress { background: var(--color-amber); }
.task-status.done { background: var(--color-green); }
.task-title, .idea-title { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.task-agent { font-size: 0.72rem; }
.idea-votes { font-size: 0.78rem; flex-shrink: 0; }
.agent-health-list { display: flex; flex-direction: column; gap: 0.4rem; }
.ah-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; }
.ah-name { font-weight: 500; }
.ah-role { flex: 1; font-size: 0.78rem; }
.ah-dot { width: 8px; height: 8px; border-radius: 50%; }
.ah-dot.online { background: var(--color-green); }
.ah-dot.idle   { background: var(--color-amber); }
.ah-dot.offline { background: var(--color-text-dim); }
.dim { color: var(--color-text-dim); font-size: 0.78rem; }
@media (max-width: 640px) { .row { grid-template-columns: 1fr; } }
</style>
