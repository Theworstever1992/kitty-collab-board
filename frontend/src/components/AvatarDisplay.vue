<template>
  <div class="avatar-wrap">
    <div v-if="svgContent" class="avatar-svg" v-html="svgContent" />
    <div v-else class="avatar-fallback">{{ initials }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ avatarSvg?: string | null; name: string; size?: number }>()

const ALLOWED_TAGS = new Set(['svg','g','path','circle','rect','ellipse','polygon','polyline','line','text','tspan','defs','use','symbol','title','desc'])

function sanitizeSvg(raw: string): string | null {
  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(raw, 'image/svg+xml')
    if (doc.querySelector('parsererror')) return null
    // Remove scripts and event attributes
    doc.querySelectorAll('script').forEach(n => n.remove())
    doc.querySelectorAll('*').forEach(el => {
      Array.from(el.attributes).forEach(attr => {
        if (attr.name.startsWith('on') || attr.name === 'href' && attr.value.startsWith('javascript')) {
          el.removeAttribute(attr.name)
        }
      })
      if (!ALLOWED_TAGS.has(el.tagName.toLowerCase())) el.remove()
    })
    return doc.documentElement.outerHTML
  } catch { return null }
}

const svgContent = computed(() => props.avatarSvg ? sanitizeSvg(props.avatarSvg) : null)
const initials = computed(() => props.name.slice(0, 2).toUpperCase())
</script>

<style scoped>
.avatar-wrap {
  width: v-bind('(props.size ?? 40) + "px"');
  height: v-bind('(props.size ?? 40) + "px"');
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-surface-2);
}
.avatar-svg { width: 100%; height: 100%; }
.avatar-svg :deep(svg) { width: 100%; height: 100%; }
.avatar-fallback {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75em; font-weight: 700;
  color: var(--color-amber);
}
</style>
