<template>
  <div class="export-import">
    <div class="row">
      <button class="btn-ghost" @click="exportAgent('json')">⬇️ JSON</button>
      <button class="btn-ghost" @click="exportAgent('md')">⬇️ Markdown</button>
      <label class="btn-ghost import-btn">
        ⬆️ Import
        <input type="file" accept=".json" @change="importAgent" style="display:none" />
      </label>
    </div>
    <div v-if="msg" class="msg" :class="{ err: isErr }">{{ msg }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ agentName: string }>()
const emit = defineEmits<{ (e: 'imported'): void }>()
const msg = ref('')
const isErr = ref(false)

async function exportAgent(fmt: 'json' | 'md') {
  const res = await fetch(`/api/v2/agents/${props.agentName}/export?format=${fmt}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `${props.agentName}.${fmt}`; a.click()
  URL.revokeObjectURL(url)
}

async function importAgent(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]; if (!file) return
  const text = await file.text()
  try {
    const body = JSON.parse(text)
    const res = await fetch('/api/v2/agents/import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    if (res.ok) { msg.value = 'Imported ✅'; isErr.value = false; emit('imported') }
    else { msg.value = `Error: ${res.status}`; isErr.value = true }
  } catch { msg.value = 'Invalid JSON'; isErr.value = true }
}
</script>

<style scoped>
.export-import { display: flex; flex-direction: column; gap: 0.5rem; }
.row { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.import-btn { cursor: pointer; }
.msg { font-size: 0.8rem; padding: 0.25rem 0; }
.msg.err { color: #e56; }
</style>
