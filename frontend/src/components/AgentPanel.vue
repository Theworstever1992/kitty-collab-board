<template>
  <aside class="agent-panel">
    <div class="panel-header">🐾 Online</div>
    <ul class="agent-list">
      <li v-for="agent in agents" :key="agent.name" class="agent-row">
        <span class="status-dot" :class="dotClass(agent.name)" />
        <span class="agent-name">{{ agent.name }}</span>
        <span class="agent-role">{{ agent.role }}</span>
      </li>
    </ul>
    <div v-if="agents.length === 0" class="empty">No agents online</div>
  </aside>
</template>

<script setup lang="ts">
import type { Agent, AgentStatus } from '../types'

const props = defineProps<{
  agents: Agent[]
  presence: Record<string, AgentStatus>
}>()

function dotClass(name: string) {
  const s = props.presence[name] ?? 'offline'
  return { online: s === 'online', idle: s === 'idle', offline: s === 'offline' }
}
</script>

<style scoped>
.agent-panel {
  width: var(--right-panel-width);
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  flex-shrink: 0;
}
.panel-header {
  padding: 1rem;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-dim);
  border-bottom: 1px solid var(--color-border);
}
.agent-list { list-style: none; padding: 0.5rem; }
.agent-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.25rem;
  font-size: 0.8rem;
}
.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-dot.online  { background: var(--color-green); }
.status-dot.idle    { background: var(--color-amber); }
.status-dot.offline { background: var(--color-text-dim); }
.agent-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.agent-role { font-size: 0.7rem; color: var(--color-text-dim); }
.empty { padding: 1rem; font-size: 0.8rem; color: var(--color-text-dim); }
</style>
