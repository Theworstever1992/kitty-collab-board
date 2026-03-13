<template>
  <div class="taskboard">
    <h2>📋 Task Board</h2>
    <div v-if="loading" class="dim">Loading…</div>
    <div v-else class="kanban">
      <div v-for="col in columns" :key="col.key" class="column">
        <div class="col-header">
          <span class="col-title">{{ col.label }}</span>
          <span class="col-count">{{ col.tasks.length }}</span>
        </div>
        <div class="col-tasks">
          <div
            v-for="task in col.tasks" :key="task.id"
            class="task-card"
            :draggable="true"
            @dragstart="onDragStart(task)"
            @drop.prevent="onDrop(col.key)"
            @dragover.prevent
          >
            <div class="task-title">{{ task.title }}</div>
            <div class="task-meta">
              <span class="task-team dim">{{ task.team_id }}</span>
              <AvatarDisplay v-if="task.assigned_to" :name="task.assigned_to" :size="20" />
            </div>
            <div class="task-tags" v-if="task.tags?.length">
              <span v-for="tag in task.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
          <div class="col-drop-zone" v-if="col.tasks.length === 0">
            <span class="dim">Drop tasks here</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/client'
import AvatarDisplay from '../components/AvatarDisplay.vue'
import type { Task } from '../types'

const tasks = ref<Task[]>([])
const loading = ref(true)
const dragging = ref<Task | null>(null)

const columns = computed(() => [
  { key: 'pending',     label: '📥 Pending',     tasks: tasks.value.filter(t => t.status === 'pending') },
  { key: 'in_progress', label: '⚡ In Progress',  tasks: tasks.value.filter(t => t.status === 'in_progress') },
  { key: 'done',        label: '✅ Done',         tasks: tasks.value.filter(t => t.status === 'done') },
])

function onDragStart(task: Task) { dragging.value = task }

async function onDrop(status: string) {
  const task = dragging.value; if (!task || task.status === status) return
  const old = task.status; task.status = status as Task['status']
  const res = await fetch(`/api/v2/tasks/${task.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) })
  if (!res.ok) task.status = old
  dragging.value = null
}

onMounted(async () => {
  const res = await api.getTasks()
  if (res.ok) tasks.value = res.data
  loading.value = false
})
</script>

<style scoped>
.taskboard { padding: 1.5rem; overflow-x: auto; height: 100%; }
h2 { color: var(--color-amber); font-size: 1.1rem; margin-bottom: 1.25rem; }
.kanban { display: flex; gap: 1rem; min-height: 400px; align-items: flex-start; }
.column { flex: 0 0 260px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); display: flex; flex-direction: column; }
.col-header { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem; border-bottom: 1px solid var(--color-border); }
.col-title { font-weight: 600; font-size: 0.875rem; }
.col-count { background: var(--color-surface-2); border-radius: 99px; padding: 0.1rem 0.5rem; font-size: 0.72rem; color: var(--color-text-dim); }
.col-tasks { padding: 0.5rem; display: flex; flex-direction: column; gap: 0.5rem; flex: 1; min-height: 100px; }
.task-card { background: var(--color-surface-2); border: 1px solid var(--color-border); border-radius: var(--radius); padding: 0.75rem; cursor: grab; transition: border-color 0.15s; }
.task-card:hover { border-color: var(--color-amber); }
.task-title { font-size: 0.875rem; font-weight: 500; margin-bottom: 0.4rem; }
.task-meta { display: flex; align-items: center; justify-content: space-between; }
.task-team { font-size: 0.72rem; }
.task-tags { display: flex; flex-wrap: wrap; gap: 0.25rem; margin-top: 0.4rem; }
.tag { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 99px; padding: 0.1rem 0.5rem; font-size: 0.68rem; color: var(--color-text-dim); }
.col-drop-zone { flex: 1; display: flex; align-items: center; justify-content: center; padding: 1rem; }
.dim { color: var(--color-text-dim); font-size: 0.78rem; }
</style>
