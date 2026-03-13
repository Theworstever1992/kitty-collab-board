<template>
  <div class="editor">
    <h3>Edit Profile</h3>
    <label>Bio
      <textarea v-model="form.bio" rows="3" placeholder="Short bio…" />
    </label>
    <label>Skills <span class="hint">(comma separated)</span>
      <input v-model="skillsInput" placeholder="python, rag, qa" />
    </label>
    <label>Personality seed
      <input v-model="form.personality_seed" placeholder="curious, detail-oriented…" />
    </label>
    <label class="avatar-label">
      Avatar SVG
      <input type="file" accept=".svg" @change="onFile" />
      <span class="hint">Max 50 KB, SVG only</span>
      <span v-if="avatarError" class="err">{{ avatarError }}</span>
    </label>
    <div class="btn-row">
      <button class="btn-primary" :disabled="saving" @click="save">
        {{ saving ? 'Saving…' : '💾 Save' }}
      </button>
      <button class="btn-ghost" @click="$emit('cancel')">Cancel</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { api } from '../api/client'
import type { Agent } from '../types'

const props = defineProps<{ agent: Agent }>()
const emit = defineEmits<{ (e: 'saved', a: Agent): void; (e: 'cancel'): void }>()

const form = reactive({
  bio: (props.agent as any).bio ?? '',
  personality_seed: (props.agent as any).personality_seed ?? '',
  avatar_svg: (props.agent as any).avatar_svg ?? '',
})
const skillsInput = ref(((props.agent as any).skills ?? []).join(', '))
const avatarError = ref('')
const saving = ref(false)

function onFile(e: Event) {
  avatarError.value = ''
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!file.name.endsWith('.svg')) { avatarError.value = 'SVG files only'; return }
  if (file.size > 51200) { avatarError.value = 'File must be ≤ 50 KB'; return }
  const reader = new FileReader()
  reader.onload = () => { form.avatar_svg = reader.result as string }
  reader.readAsText(file)
}

async function save() {
  saving.value = true
  const payload = {
    bio: form.bio,
    personality_seed: form.personality_seed,
    skills: skillsInput.value.split(',').map((s: string) => s.trim()).filter(Boolean),
    avatar_svg: form.avatar_svg || undefined,
  }
  const res = await api.updateProfile(props.agent.name, payload)
  saving.value = false
  if (res.ok) emit('saved', res.data)
}
</script>

<style scoped>
.editor { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 1.25rem; margin-bottom: 1.5rem; }
h3 { color: var(--color-amber); margin-bottom: 1rem; font-size: 0.95rem; }
label { display: flex; flex-direction: column; gap: 0.3rem; margin-bottom: 0.9rem; font-size: 0.85rem; color: var(--color-text-dim); }
textarea, input { background: var(--color-surface-2); border: 1px solid var(--color-border); border-radius: var(--radius); padding: 0.4rem 0.6rem; color: var(--color-text); font-size: 0.875rem; resize: vertical; }
.hint { font-size: 0.72rem; color: var(--color-text-dim); }
.err { color: #e56; font-size: 0.8rem; }
.avatar-label { gap: 0.4rem; }
.btn-row { display: flex; gap: 0.75rem; margin-top: 0.5rem; }
</style>
