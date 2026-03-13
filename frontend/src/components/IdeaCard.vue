<template>
  <div class="idea-card" @click="$emit('click')">
    <div class="idea-top">
      <AvatarDisplay :name="idea.author" :size="28" />
      <div class="idea-author">{{ idea.author }}</div>
      <span class="idea-status" :class="idea.status">{{ idea.status }}</span>
    </div>
    <div class="idea-title">{{ idea.title }}</div>
    <div class="idea-body" v-if="idea.body">{{ idea.body.slice(0, 140) }}{{ idea.body.length > 140 ? '…' : '' }}</div>
    <div class="idea-footer">
      <button class="vote-btn" :class="{ voted: idea.user_voted }" @click.stop="vote">
        🐾 {{ idea.reaction_count }}
      </button>
      <span class="idea-age">{{ age }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AvatarDisplay from './AvatarDisplay.vue'
import type { Idea } from '../types'

const props = defineProps<{ idea: Idea }>()
const emit = defineEmits<{ (e: 'vote'): void; (e: 'click'): void }>()

const age = computed(() => {
  const ms = Date.now() - new Date(props.idea.created_at).getTime()
  const h = Math.floor(ms / 3600000)
  return h < 1 ? 'just now' : h < 24 ? `${h}h ago` : `${Math.floor(h / 24)}d ago`
})

function vote() { emit('vote') }
</script>

<style scoped>
.idea-card {
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--radius-lg); padding: 1rem; cursor: pointer;
  transition: border-color 0.15s; display: flex; flex-direction: column; gap: 0.5rem;
}
.idea-card:hover { border-color: var(--color-amber); }
.idea-top { display: flex; align-items: center; gap: 0.5rem; }
.idea-author { font-size: 0.8rem; color: var(--color-text-dim); flex: 1; }
.idea-status { font-size: 0.7rem; border-radius: 99px; padding: 0.1rem 0.5rem; font-weight: 600; }
.idea-status.pending  { background: #78350f33; color: #fbbf24; }
.idea-status.approved { background: #14532d33; color: #4ade80; }
.idea-status.rejected { background: #4c0519; color: #f87171; }
.idea-title { font-weight: 600; font-size: 0.95rem; }
.idea-body { font-size: 0.8rem; color: var(--color-text-dim); line-height: 1.4; }
.idea-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 0.25rem; }
.vote-btn { background: var(--color-surface-2); border: 1px solid var(--color-border); border-radius: 99px; padding: 0.2rem 0.7rem; font-size: 0.8rem; cursor: pointer; color: var(--color-text-dim); transition: all 0.15s; }
.vote-btn.voted { border-color: var(--color-amber); color: var(--color-amber); background: #78350f22; }
.idea-age { font-size: 0.72rem; color: var(--color-text-dim); }
</style>
