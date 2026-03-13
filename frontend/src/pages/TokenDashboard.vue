<template>
  <div class="tokens">
    <h2>💰 Token Dashboard</h2>
    <div v-if="loading" class="dim">Loading…</div>
    <div v-else>
      <div class="summary">
        <div class="stat"><span class="val">${{ totalUsd.toFixed(4) }}</span><span class="lbl">Total USD</span></div>
        <div class="stat"><span class="val">{{ totalIn.toLocaleString() }}</span><span class="lbl">Input tokens</span></div>
        <div class="stat"><span class="val">{{ totalOut.toLocaleString() }}</span><span class="lbl">Output tokens</span></div>
      </div>
      <div class="agent-list">
        <div v-for="row in rows" :key="row.agent" class="agent-row">
          <div class="agent-name">{{ row.agent }}</div>
          <div class="bar-wrap">
            <div class="bar" :style="{ width: barPct(row) + '%', background: barColor(row) }" />
          </div>
          <div class="agent-stats">
            <span>${{ row.total_cost_usd.toFixed(4) }}</span>
            <span class="dim">{{ (row.total_input_tokens ?? 0).toLocaleString() }} in / {{ (row.total_output_tokens ?? 0).toLocaleString() }} out</span>
            <span v-if="row.daily_budget_usd" class="budget" :class="{ over: row.total_cost_usd > row.daily_budget_usd }">
              budget ${{ row.daily_budget_usd }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/client'
import type { TokenBudget } from '../types'

const rows = ref<TokenBudget[]>([])
const loading = ref(true)

const totalUsd = computed(() => rows.value.reduce((s, r) => s + (r.total_cost_usd ?? 0), 0))
const totalIn  = computed(() => rows.value.reduce((s, r) => s + (r.total_input_tokens ?? 0), 0))
const totalOut = computed(() => rows.value.reduce((s, r) => s + (r.total_output_tokens ?? 0), 0))
const maxUsd   = computed(() => Math.max(...rows.value.map(r => r.total_cost_usd ?? 0), 0.0001))

function barPct(row: TokenBudget) { return Math.min(100, ((row.total_cost_usd ?? 0) / maxUsd.value) * 100) }
function barColor(row: TokenBudget) {
  if (!row.daily_budget_usd) return 'var(--color-amber)'
  return row.total_cost_usd > row.daily_budget_usd ? '#f87171' : 'var(--color-green)'
}

onMounted(async () => {
  const res = await api.getTokenReport()
  if (res.ok) rows.value = Array.isArray(res.data) ? res.data : [res.data]
  loading.value = false
})
</script>

<style scoped>
.tokens { padding: 1.5rem; overflow-y: auto; height: 100%; }
h2 { color: var(--color-amber); font-size: 1.1rem; margin-bottom: 1.25rem; }
.summary { display: flex; gap: 1.5rem; margin-bottom: 1.5rem; }
.stat { display: flex; flex-direction: column; }
.val { font-size: 1.1rem; font-weight: 700; color: var(--color-amber); }
.lbl { font-size: 0.72rem; color: var(--color-text-dim); }
.agent-list { display: flex; flex-direction: column; gap: 0.75rem; }
.agent-row { display: grid; grid-template-columns: 100px 1fr 200px; gap: 0.75rem; align-items: center; }
.agent-name { font-size: 0.875rem; font-weight: 500; }
.bar-wrap { background: var(--color-surface-2); border-radius: 99px; height: 8px; overflow: hidden; }
.bar { height: 100%; border-radius: 99px; transition: width 0.4s; }
.agent-stats { display: flex; gap: 0.5rem; font-size: 0.78rem; flex-wrap: wrap; }
.dim { color: var(--color-text-dim); }
.budget { font-size: 0.72rem; }
.budget.over { color: #f87171; }
</style>
