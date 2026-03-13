<template>
  <nav class="sidebar">
    <div class="sidebar-header">
      <span class="logo">🐱 Clowder</span>
    </div>

    <div class="section-label">Channels</div>
    <ul class="channel-list">
      <li
        v-for="ch in channels"
        :key="ch.name"
        class="channel-item"
        :class="{ active: ch.name === activeRoom }"
        @click="$emit('select', ch.name)"
      >
        <span class="hash">#</span>
        <span class="name">{{ ch.name }}</span>
        <span v-if="ch.unread_count" class="unread-badge">{{ ch.unread_count }}</span>
      </li>
    </ul>

    <div class="section-label">Navigation</div>
    <ul class="nav-list">
      <li @click="$router.push('/dashboard')">🏠 Dashboard</li>
      <li @click="$router.push('/tasks')">📋 Tasks</li>
      <li @click="$router.push('/ideas')">💡 Ideas</li>
      <li @click="$router.push('/agents')">🐾 Agents</li>
      <li @click="$router.push('/teams')">🐱 Teams</li>
      <li @click="$router.push('/meetings')">📅 Meetings</li>
      <li @click="$router.push('/tokens')">💰 Tokens</li>
      <li @click="$router.push('/violations')">⚠️ Violations</li>
    </ul>
  </nav>
</template>

<script setup lang="ts">
import type { Channel } from '../types'

defineProps<{ channels: Channel[]; activeRoom: string }>()
defineEmits<{ select: [room: string] }>()
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  flex-shrink: 0;
}
.sidebar-header {
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
}
.logo { font-size: 1rem; font-weight: 700; color: var(--color-amber); }
.section-label {
  padding: 0.75rem 1rem 0.25rem;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-dim);
}
.channel-list, .nav-list { list-style: none; padding: 0 0.5rem; }
.channel-item, .nav-list li {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.35rem 0.5rem;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text-dim);
  transition: background 0.1s, color 0.1s;
}
.channel-item:hover, .nav-list li:hover { background: var(--color-surface-2); color: var(--color-text); }
.channel-item.active { background: var(--color-surface-2); color: var(--color-amber); }
.hash { color: var(--color-text-dim); font-size: 0.8rem; }
.name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.unread-badge {
  background: var(--color-amber);
  color: var(--color-bg);
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 99px;
}
.nav-list li { gap: 0.5rem; }
</style>
