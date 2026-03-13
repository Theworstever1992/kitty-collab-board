<template>
  <ChatRoom :room="room" agent-name="human" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import ChatRoom from '../components/ChatRoom.vue'

const route = useRoute()
const room = computed(() => route.params.room as string)
</script>
