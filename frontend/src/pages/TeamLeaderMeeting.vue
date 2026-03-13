<template>
  <div class="meetings">
    <h2>🐱 Leader Meetings</h2>
    <div v-if="loading" class="dim">Loading…</div>
    <div v-else-if="meetings.length === 0" class="dim">No meetings yet.</div>
    <div v-else class="list">
      <div v-for="m in meetings" :key="m.id" class="meeting-card">
        <div class="meeting-header">
          <span class="ts">{{ fmtDate(m.created_at) }}</span>
          <div class="participants">
            <AvatarDisplay v-for="p in m.participants" :key="p" :name="p" :size="22" />
          </div>
        </div>
        <div class="agenda" v-if="m.agenda?.length">
          <div class="section-label">Agenda</div>
          <ul><li v-for="(item, i) in m.agenda" :key="i">{{ item }}</li></ul>
        </div>
        <div class="decisions" v-if="m.decisions?.length">
          <div class="section-label">Decisions</div>
          <ul><li v-for="(d, i) in m.decisions" :key="i">{{ d }}</li></ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AvatarDisplay from '../components/AvatarDisplay.vue'

interface Meeting { id: string; agenda: string[]; participants: string[]; decisions: string[]; created_at: string }

const meetings = ref<Meeting[]>([])
const loading = ref(true)

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  try {
    const res = await fetch('/api/v2/meetings')
    if (res.ok) meetings.value = await res.json()
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.meetings { padding: 1.5rem; overflow-y: auto; height: 100%; }
h2 { color: var(--color-amber); font-size: 1.1rem; margin-bottom: 1.25rem; }
.list { display: flex; flex-direction: column; gap: 1rem; }
.meeting-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 1rem; }
.meeting-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; }
.ts { font-size: 0.8rem; color: var(--color-text-dim); }
.participants { display: flex; gap: 0.25rem; }
.section-label { font-size: 0.72rem; color: var(--color-text-dim); font-weight: 600; text-transform: uppercase; margin-bottom: 0.35rem; }
ul { margin: 0 0 0.75rem 1rem; padding: 0; font-size: 0.85rem; line-height: 1.5; color: var(--color-cream-dim); }
.dim { color: var(--color-text-dim); padding: 2rem; }
</style>
