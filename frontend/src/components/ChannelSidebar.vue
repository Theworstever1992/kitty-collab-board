<template>
  <nav class="sidebar">
    <div class="sidebar-header">
      <span class="logo">🐱 Clowder</span>
    </div>

    <div class="section-label" id="channels-label">Channels</div>
    <ul class="channel-list" aria-labelledby="channels-label">
      <li
        v-for="ch in channels"
        :key="ch.name"
      >
        <button
          class="channel-item"
          :class="{ active: ch.name === activeRoom }"
          :aria-current="ch.name === activeRoom ? 'page' : undefined"
          @click="$emit('select', ch.name)"
        >
          <span class="hash" aria-hidden="true">#</span>
          <span class="name">{{ ch.name }}</span>
          <span v-if="ch.unread_count" class="unread-badge">
            {{ ch.unread_count }}
            <span class="sr-only">unread messages</span>
          </span>
        </button>
      </li>
    </ul>

    <div class="section-label" id="nav-label">Navigation</div>
    <ul class="nav-list" aria-labelledby="nav-label">
      <li>
        <button class="nav-btn" @click="$router.push('/dashboard')">
          <span aria-hidden="true">🏠</span> Dashboard
        </button>
      </li>
      <li>
        <button class="nav-btn" @click="$router.push('/tasks')">
          <span aria-hidden="true">📋</span> Tasks
        </button>
      </li>
      <li>
        <button class="nav-btn" @click="$router.push('/ideas')">
          <span aria-hidden="true">💡</span> Ideas
        </button>
      </li>
      <li>
        <button class="nav-btn" @click="$router.push('/agents')">
          <span aria-hidden="true">🐾</span> Agents
        </button>
      </li>
      <li>
        <button class="nav-btn" @click="$router.push('/teams')">
          <span aria-hidden="true">🐱</span> Teams
        </button>
      </li>
      <li>
        <button class="nav-btn" @click="$router.push('/meetings')">
          <span aria-hidden="true">📅</span> Meetings
        </button>
      </li>
      <li>
        <button class="nav-btn" @click="$router.push('/tokens')">
          <span aria-hidden="true">💰</span> Tokens
        </button>
      </li>
      <li>
        <button class="nav-btn" @click="$router.push('/violations')">
          <span aria-hidden="true">⚠️</span> Violations
        </button>
      </li>
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

.channel-item, .nav-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.35rem 0.5rem;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text-dim);
  transition: background 0.1s, color 0.1s;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
}

.channel-item:hover, .nav-btn:hover {
  background: var(--color-surface-2);
  color: var(--color-text);
}

.channel-item.active {
  background: var(--color-surface-2);
  color: var(--color-amber);
}

.nav-btn {
  gap: 0.5rem;
}

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
</style>
