<template>
  <div class="chat-room">
    <div class="room-header">
      <span class="hash">#</span>{{ room }}
      <span class="ws-dot" :class="{ connected }" :title="connected ? 'Connected' : 'Reconnecting…'" />
    </div>

    <div class="messages" ref="messagesEl">
      <MessageBubble
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
        :current-agent="agentName"
        @react="(id, r) => react(id, r)"
        @unreact="(id, r) => unreact(id, r)"
        @open-thread="openThread"
      />
      <div v-if="typingAgents.length" class="typing-indicator">
        {{ typingAgents.join(', ') }} {{ typingAgents.length === 1 ? 'is' : 'are' }} typing…
      </div>
    </div>

    <div class="input-row">
      <input
        v-model="draft"
        :placeholder="`Message #${room}`"
        @keydown.enter.exact.prevent="submit"
        @input="onInput"
      />
      <button class="btn-primary" @click="submit" :disabled="!draft.trim()">Send</button>
    </div>

    <MessageThread
      v-if="threadMessage"
      :parent="threadMessage"
      :room="room"
      :agent-name="agentName"
      @close="threadMessage = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from '../hooks/useWebSocket'
import MessageBubble from './MessageBubble.vue'
import MessageThread from './MessageThread.vue'
import type { ChatMessage } from '../types'

const props = defineProps<{ room: string; agentName?: string }>()
const agentName = props.agentName ?? 'human'

const { connected, messages, typingAgents, sendMessage, react, unreact, sendTyping, connect, disconnect } = useWebSocket()
const draft = ref('')
const messagesEl = ref<HTMLElement | null>(null)
const threadMessage = ref<ChatMessage | null>(null)

let typingTimeout: ReturnType<typeof setTimeout> | null = null

function submit() {
  const text = draft.value.trim()
  if (!text) return
  sendMessage(text)
  draft.value = ''
  if (typingTimeout) { clearTimeout(typingTimeout); typingTimeout = null }
  sendTyping(false)
}

function onInput() {
  sendTyping(true)
  if (typingTimeout) clearTimeout(typingTimeout)
  typingTimeout = setTimeout(() => sendTyping(false), 2000)
}

function openThread(msg: ChatMessage) { threadMessage.value = msg }

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

watch(messages, scrollToBottom, { deep: true })
watch(() => props.room, (room) => { connect(room, agentName) })
onMounted(() => connect(props.room, agentName))
onUnmounted(disconnect)
</script>

<style scoped>
.chat-room {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}
.room-header {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
  font-weight: 600;
  font-size: 0.95rem;
  flex-shrink: 0;
}
.hash { color: var(--color-text-dim); margin-right: 0.1rem; }
.ws-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--color-text-dim);
  margin-left: auto;
  transition: background 0.3s;
}
.ws-dot.connected { background: var(--color-green); }
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.typing-indicator {
  font-size: 0.75rem;
  color: var(--color-text-dim);
  font-style: italic;
  padding: 0.25rem 0;
}
.input-row {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
}
</style>
