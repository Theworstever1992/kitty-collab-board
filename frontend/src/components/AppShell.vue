<template>
  <div class="app-shell">
    <ChannelSidebar :channels="channels" :active-room="activeRoom" @select="navigateTo" />
    <main class="main-area">
      <router-view />
    </main>
    <AgentPanel :agents="agents" :presence="presence" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import ChannelSidebar from './ChannelSidebar.vue'
import AgentPanel from './AgentPanel.vue'
import { api } from '../api/client'
import type { Agent, Channel } from '../types'
import type { AgentStatus } from '../types'

const router = useRouter()
const route = useRoute()
const channels = ref<Channel[]>([])
const agents = ref<Agent[]>([])
const presence = ref<Record<string, AgentStatus>>({})

const activeRoom = ref((route.params.room as string) ?? 'main-hall')

async function load() {
  const [ch, ag] = await Promise.all([api.getChannels(), api.getAgents()])
  if (ch.ok) channels.value = ch.data
  if (ag.ok) {
    agents.value = ag.data
    ag.data.forEach(a => { presence.value[a.name] = a.status })
  }
}

function navigateTo(room: string) {
  activeRoom.value = room
  router.push(`/chat/${room}`)
}

onMounted(load)
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}
.main-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
