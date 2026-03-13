<template>
  <div class="bubble" :class="{ self: isSelf }">
    <div class="meta">
      <span class="sender">{{ message.sender }}</span>
      <span class="type-badge" v-if="message.type !== 'chat'">{{ message.type }}</span>
      <span class="time">{{ formatTime(message.timestamp) }}</span>
    </div>
    <div class="content" v-html="renderContent(message.content)" />
    <div class="footer">
      <ReactionBar
        :reactions="message.reactions ?? {}"
        :current-agent="currentAgent"
        @react="(r) => $emit('react', message.id, r)"
        @unreact="(r) => $emit('unreact', message.id, r)"
      />
      <button
        v-if="(message.reply_count ?? 0) > 0"
        class="thread-btn"
        @click="$emit('open-thread', message)"
      >
        💬 {{ message.reply_count }} {{ message.reply_count === 1 ? 'reply' : 'replies' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import ReactionBar from './ReactionBar.vue'
import type { ChatMessage } from '../types'

const props = defineProps<{ message: ChatMessage; currentAgent: string }>()
defineEmits<{
  react: [id: string, reaction: string]
  unreact: [id: string, reaction: string]
  'open-thread': [message: ChatMessage]
}>()

const isSelf = props.message.sender === props.currentAgent

function formatTime(ts: string | null) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function renderContent(content: string) {
  // Basic safe rendering: escape HTML then convert **bold** and `code`
  const escaped = content
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return escaped
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.bubble {
  max-width: 100%;
  padding: 0.4rem 0;
}
.meta {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 0.15rem;
}
.sender { font-weight: 600; font-size: 0.875rem; color: var(--color-amber); }
.bubble.self .sender { color: var(--color-blue); }
.type-badge {
  font-size: 0.65rem;
  padding: 0.1rem 0.35rem;
  border-radius: 3px;
  background: var(--color-surface-2);
  color: var(--color-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.time { font-size: 0.72rem; color: var(--color-text-dim); margin-left: auto; }
.content {
  font-size: 0.875rem;
  line-height: 1.5;
  word-break: break-word;
}
.content :deep(strong) { color: var(--color-cream); }
.content :deep(code) {
  font-family: var(--font-mono);
  font-size: 0.8em;
  background: var(--color-surface-2);
  padding: 0.1em 0.3em;
  border-radius: 3px;
}
.footer { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.2rem; }
.thread-btn {
  background: transparent;
  color: var(--color-text-dim);
  font-size: 0.75rem;
  padding: 0.15rem 0.4rem;
  border-radius: var(--radius);
}
.thread-btn:hover { background: var(--color-surface-2); color: var(--color-amber); }
</style>
