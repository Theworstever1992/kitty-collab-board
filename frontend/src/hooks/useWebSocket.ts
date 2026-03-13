import { ref, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import type { ChatMessage, AgentStatus, ReactionMap } from '../types'

interface UseWebSocket {
  connected: Ref<boolean>
  messages: Ref<ChatMessage[]>
  typingAgents: Ref<string[]>
  presence: Ref<Record<string, AgentStatus>>
  sendMessage: (content: string, messageType?: string, threadId?: string | null) => void
  react: (messageId: string, reaction: string) => void
  unreact: (messageId: string, reaction: string) => void
  sendTyping: (isTyping: boolean) => void
  connect: (room: string, agent: string) => void
  disconnect: () => void
}

export function useWebSocket(): UseWebSocket {
  const connected = ref(false)
  const messages = ref<ChatMessage[]>([])
  const typingAgents = ref<string[]>([])
  const presence = ref<Record<string, AgentStatus>>({})

  let ws: WebSocket | null = null
  let currentRoom = ''
  let currentAgent = ''
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectDelay = 1000
  let typingTimers: Record<string, ReturnType<typeof setTimeout>> = {}

  function send(frame: object) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(frame))
    }
  }

  function handleMessage(raw: string) {
    let frame: Record<string, unknown>
    try { frame = JSON.parse(raw) } catch { return }

    switch (frame.type) {
      case 'connected': {
        const history = (frame.recent_messages as ChatMessage[]) ?? []
        messages.value = history
        break
      }
      case 'message': {
        const msg = frame.data as ChatMessage
        if (!messages.value.find(m => m.id === msg.id)) {
          messages.value.push(msg)
        }
        break
      }
      case 'reaction': {
        const target = messages.value.find(m => m.id === frame.message_id)
        if (target) target.reactions = frame.reactions as ReactionMap
        break
      }
      case 'thread_reply': {
        const target = messages.value.find(m => m.id === frame.parent_id)
        if (target) target.reply_count = frame.reply_count as number
        break
      }
      case 'typing': {
        const agent = frame.agent as string
        const isTyping = frame.is_typing as boolean
        if (isTyping) {
          if (!typingAgents.value.includes(agent)) typingAgents.value.push(agent)
          clearTimeout(typingTimers[agent])
          typingTimers[agent] = setTimeout(() => {
            typingAgents.value = typingAgents.value.filter(a => a !== agent)
          }, 3000)
        } else {
          typingAgents.value = typingAgents.value.filter(a => a !== agent)
        }
        break
      }
      case 'presence': {
        presence.value[frame.agent as string] = frame.status as AgentStatus
        break
      }
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      if (currentRoom) connect(currentRoom, currentAgent)
    }, reconnectDelay)
    reconnectDelay = Math.min(reconnectDelay * 2, 30000)
  }

  function connect(room: string, agent: string) {
    currentRoom = room
    currentAgent = agent
    disconnect()

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    ws = new WebSocket(`${protocol}://${window.location.host}/ws/${room}`)

    ws.onopen = () => {
      connected.value = true
      reconnectDelay = 1000
      send({ type: 'auth', agent, token: null })
    }
    ws.onmessage = (e) => handleMessage(e.data)
    ws.onclose = () => {
      connected.value = false
      scheduleReconnect()
    }
    ws.onerror = () => {
      connected.value = false
    }
  }

  function disconnect() {
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
    ws?.close()
    ws = null
    connected.value = false
    messages.value = []
    typingAgents.value = []
  }

  function sendMessage(content: string, messageType = 'chat', threadId: string | null = null) {
    send({ type: 'message', room: currentRoom, sender: currentAgent, content, message_type: messageType, thread_id: threadId })
  }

  function react(messageId: string, reaction: string) {
    send({ type: 'react', room: currentRoom, message_id: messageId, reactor: currentAgent, reaction })
  }

  function unreact(messageId: string, reaction: string) {
    send({ type: 'unreact', room: currentRoom, message_id: messageId, reactor: currentAgent, reaction })
  }

  function sendTyping(isTyping: boolean) {
    send({ type: 'typing', room: currentRoom, agent: currentAgent, is_typing: isTyping })
  }

  onUnmounted(disconnect)

  return { connected, messages, typingAgents, presence, sendMessage, react, unreact, sendTyping, connect, disconnect }
}
