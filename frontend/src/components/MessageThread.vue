<template>
  <div class="thread-overlay" @click.self="$emit('close')">
    <div class="thread-panel">
      <div class="thread-header">
        <span>🧵 Thread</span>
        <button class="btn-ghost close-btn" @click="$emit('close')" aria-label="Close thread">✕</button>
      </div>

      <div class="parent-message">
        <MessageBubble :message="parent" :current-agent="agentName" @react="() => {}" @unreact="() => {}" @open-thread="() => {}" />
      </div>

      <div class="replies" ref="repliesEl">
        <MessageBubble
          v-for="reply in replies"
          :key="reply.id"
          :message="reply"
          :current-agent="agentName"
          @react="(id, r) => wsReact(id, r)"
          @unreact="(id, r) => wsUnreact(id, r)"
          @open-thread="() => {}"
        />
        <div v-if="replies.length === 0" class="empty">No replies yet</div>
      </div>

      <div class="reply-input">
        <input v-model="draft" placeholder="Reply…" @keydown.enter.exact.prevent="submit" />
        <button class="btn-primary" @click="submit" :disabled="!draft.trim()">Reply</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useWebSocket } from '../hooks/useWebSocket'
import MessageBubble from './MessageBubble.vue'
import type { ChatMessage } from '../types'

const props = defineProps<{ parent: ChatMessage; room: string; agentName: string }>()
defineEmits(['close'])

const { messages, sendMessage, react: wsReact, unreact: wsUnreact, connect } = useWebSocket()
const draft = ref('')
const repliesEl = ref<HTMLElement | null>(null)

const replies = computed(() =>
  messages.value.filter(m => m.thread_id === props.parent.id)
)

function submit() {
  const text = draft.value.trim()
  if (!text) return
  sendMessage(text, 'chat', props.parent.id)
  draft.value = ''
}

async function scrollBottom() {
  await nextTick()
  if (repliesEl.value) repliesEl.value.scrollTop = repliesEl.value.scrollHeight
}

watch(replies, scrollBottom, { deep: true })
connect(props.room, props.agentName)
</script>

<style scoped>
.thread-overlay {
  position: fixed; inset: 0; z-index: 40;
  background: rgba(0,0,0,0.4);
  display: flex; justify-content: flex-end;
}
.thread-panel {
  width: 380px;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  display: flex; flex-direction: column;
  height: 100%;
}
.thread-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
  font-weight: 600;
}
.close-btn { font-size: 1rem; }
.parent-message {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-2);
}
.replies { flex: 1; overflow-y: auto; padding: 0.75rem 1rem; }
.empty { font-size: 0.85rem; color: var(--color-text-dim); padding: 0.5rem 0; }
.reply-input {
  display: flex; gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--color-border);
}
</style>
