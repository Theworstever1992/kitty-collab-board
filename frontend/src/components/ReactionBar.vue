<template>
  <div class="reaction-bar">
    <button
      v-for="[emoji, reactors] in reactionEntries"
      :key="emoji"
      class="reaction-chip"
      :class="{ reacted: reactors.includes(currentAgent) }"
      @click="toggle(emoji, reactors)"
    >
      {{ emoji }} <span class="count">{{ reactors.length }}</span>
    </button>
    <div class="emoji-picker-wrapper">
      <button class="add-btn" @click="showPicker = !showPicker" title="Add reaction">+</button>
      <div v-if="showPicker" class="emoji-picker">
        <button v-for="e in REACTIONS" :key="e" @click="pick(e)">{{ e }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ReactionMap } from '../types'

const REACTIONS = ['🐾', '✅', '❌', '🔥', '💡', '👀', '🤔', '🚀', '😸', '❤️']

const props = defineProps<{ reactions: ReactionMap; currentAgent: string }>()
const emit = defineEmits<{ react: [reaction: string]; unreact: [reaction: string] }>()

const showPicker = ref(false)
const reactionEntries = computed(() =>
  Object.entries(props.reactions).filter(([, r]) => r.length > 0)
)

function toggle(emoji: string, reactors: string[]) {
  if (reactors.includes(props.currentAgent)) emit('unreact', emoji)
  else emit('react', emoji)
}

function pick(emoji: string) {
  emit('react', emoji)
  showPicker.value = false
}
</script>

<style scoped>
.reaction-bar { display: flex; flex-wrap: wrap; gap: 0.25rem; align-items: center; }
.reaction-chip {
  display: flex; align-items: center; gap: 0.2rem;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: 99px;
  padding: 0.1rem 0.5rem;
  font-size: 0.8rem;
  color: var(--color-text);
  transition: border-color 0.1s;
}
.reaction-chip:hover { border-color: var(--color-amber-dim); }
.reaction-chip.reacted { border-color: var(--color-amber); background: #3a2d12; }
.count { font-size: 0.72rem; color: var(--color-text-dim); }
.add-btn {
  background: transparent;
  color: var(--color-text-dim);
  font-size: 0.9rem;
  padding: 0.1rem 0.4rem;
  border-radius: 99px;
  border: 1px solid transparent;
}
.add-btn:hover { background: var(--color-surface-2); border-color: var(--color-border); }
.emoji-picker-wrapper { position: relative; }
.emoji-picker {
  position: absolute;
  bottom: 100%;
  left: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 0.35rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  width: 180px;
  z-index: 50;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}
.emoji-picker button {
  background: transparent;
  font-size: 1.1rem;
  padding: 0.2rem;
  border-radius: 4px;
}
.emoji-picker button:hover { background: var(--color-surface-2); }
</style>
