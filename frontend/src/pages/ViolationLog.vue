<template>
  <div class="violations">
    <div class="viol-header">
      <h2>⚠️ Violations</h2>
      <div class="filters">
        <select v-model="filterAgent" class="sel">
          <option value="">All agents</option>
          <option v-for="a in agents" :key="a" :value="a">{{ a }}</option>
        </select>
        <select v-model="filterSeverity" class="sel">
          <option value="">All severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>
    </div>
    <div v-if="loading" class="dim">Loading…</div>
    <div v-else-if="filtered.length === 0" class="dim">No violations found 😸</div>
    <table v-else class="table">
      <thead>
        <tr>
          <th>Agent</th><th>Rule</th><th>Severity</th><th>Task</th><th>Time</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="v in filtered" :key="v.id" class="vrow">
          <td>{{ v.agent_name }}</td>
          <td>{{ v.rule }}</td>
          <td><span class="sev" :class="v.severity">{{ v.severity }}</span></td>
          <td><span class="task-link" v-if="v.task_id">{{ v.task_id.slice(0, 8) }}</span><span v-else>—</span></td>
          <td>{{ fmtDate(v.created_at) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/client'

interface Violation { id: string; agent_name: string; rule: string; severity: 'low'|'medium'|'high'; task_id?: string; created_at: string }

const violations = ref<Violation[]>([])
const loading = ref(true)
const filterAgent = ref('')
const filterSeverity = ref('')

const agents = computed(() => [...new Set(violations.value.map(v => v.agent_name))])
const filtered = computed(() => violations.value.filter(v =>
  (!filterAgent.value || v.agent_name === filterAgent.value) &&
  (!filterSeverity.value || v.severity === filterSeverity.value)
))

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  const res = await api.getViolations()
  if (res.ok) violations.value = res.data
  loading.value = false
})
</script>

<style scoped>
.violations { padding: 1.5rem; overflow-y: auto; height: 100%; }
.viol-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
h2 { color: var(--color-amber); font-size: 1.1rem; }
.filters { display: flex; gap: 0.5rem; }
.sel { background: var(--color-surface-2); border: 1px solid var(--color-border); border-radius: var(--radius); padding: 0.3rem 0.5rem; color: var(--color-text); font-size: 0.8rem; }
.dim { color: var(--color-text-dim); padding: 2rem; }
.table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th { text-align: left; padding: 0.5rem 0.75rem; color: var(--color-text-dim); font-weight: 500; border-bottom: 1px solid var(--color-border); }
.vrow td { padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--color-border); }
.sev { border-radius: 99px; padding: 0.1rem 0.5rem; font-size: 0.72rem; font-weight: 600; }
.sev.low    { background: #14532d33; color: #4ade80; }
.sev.medium { background: #78350f33; color: #fbbf24; }
.sev.high   { background: #4c0519; color: #f87171; }
.task-link { font-family: monospace; font-size: 0.78rem; color: var(--color-amber-dim); }
</style>
