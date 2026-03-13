// Clowder v2 — Shared TypeScript Types
// Mirrors the SQLAlchemy models in backend/models.py and API response shapes.
// Used by all Vue components and the useWebSocket hook.

// ── Core domain types ──────────────────────────────────────────────────────

export type TaskStatus = 'pending' | 'claimed' | 'done' | 'blocked'
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical'
export type MessageType = 'chat' | 'update' | 'alert' | 'task' | 'code' | 'approval' | 'plan'
export type AgentStatus = 'online' | 'idle' | 'offline'
export type IdeaStatus = 'pending' | 'approved' | 'rejected'

// ── Tasks ──────────────────────────────────────────────────────────────────

export interface Task {
  id: string
  title: string
  description: string | null
  status: TaskStatus
  role: string | null
  team_id: string | null
  priority: TaskPriority
  priority_order: number
  skills: string[] | null
  blocked_by: string[] | null
  claimed_by: string | null
  claimed_at: string | null       // ISO 8601
  result: string | null
  completed_at: string | null     // ISO 8601
  created_at: string | null       // ISO 8601
}

export interface ClaimRequest {
  agent_name: string
  claimed_at: string              // ISO 8601
}

export interface CompleteRequest {
  agent_name: string
  result: string
  completed_at?: string           // ISO 8601
}

// ── Agents ─────────────────────────────────────────────────────────────────

export interface Agent {
  name: string
  role: string
  model: string
  team: string | null
  status: AgentStatus
  last_seen: string | null        // ISO 8601
}

// Full profile — includes v2 fields added in Phase 4 (nullable until Qwen ships models.py update)
export interface AgentProfile extends Agent {
  bio: string | null
  skills: string[] | null
  avatar_svg: string | null       // SVG text, max 50KB
  personality_seed: string | null // Prompt engineering seed set by Team Leader
  started_at: string | null       // ISO 8601
}

export interface RegisterAgentRequest {
  name: string
  role?: string
  team?: string | null
  model?: string
}

// ── Messages ───────────────────────────────────────────────────────────────

export interface ChatMessage {
  id: string
  channel: string
  sender: string
  content: string
  type: MessageType
  thread_id: string | null
  metadata: Record<string, unknown> | null
  timestamp: string | null        // ISO 8601
  // Client-side enriched fields (not from API, added by WS handler)
  reactions?: Record<string, string[]>  // emoji → agent names
  reply_count?: number
}

export interface PostMessageRequest {
  content: string
  sender: string
  type?: MessageType
  thread_id?: string | null
}

// ── Reactions ──────────────────────────────────────────────────────────────

export type ReactionEmoji = '🐾' | '✅' | '❌' | '🔥' | '💡' | '👀' | '🤔' | '🚀' | '😸' | '❤️'

export interface ReactionRequest {
  reactor: string
  reaction: ReactionEmoji
}

export interface ReactionMap {
  [emoji: string]: string[]       // emoji → list of agent names who reacted
}

// ── Channels ───────────────────────────────────────────────────────────────

export interface Channel {
  name: string
  description: string
  message_count?: number
  unread_count?: number           // Client-side only
}

// ── Ideas ──────────────────────────────────────────────────────────────────

export interface Idea {
  id: string
  author: string
  title: string
  description: string
  status: IdeaStatus
  vote_count: number
  approved_by: string | null
  created_at: string              // ISO 8601
}

export interface CreateIdeaRequest {
  author: string
  title: string
  description: string
}

// ── Token Usage ────────────────────────────────────────────────────────────

export interface TokenUsage {
  agent: string
  model: string
  input_tokens: number
  output_tokens: number
  cost_usd: number
  logged_at: string               // ISO 8601
}

export interface TokenBudget {
  agent: string
  total_cost_usd: number
  ok: boolean
  daily_limit_usd?: number
  monthly_limit_usd?: number
}

export interface TokenReport {
  period: 'day' | 'week' | 'month' | 'all'
  group_by: 'agent' | 'model' | 'team'
  rows: Array<{
    key: string                   // agent name, model name, or team name
    input_tokens: number
    output_tokens: number
    cost_usd: number
  }>
}

// ── Governance ─────────────────────────────────────────────────────────────

export interface StandardsViolation {
  id: string
  agent: string
  task_id: string | null
  rule: string
  severity: 'warning' | 'error' | 'critical'
  description: string
  logged_at: string               // ISO 8601
}

// ── Conflicts ──────────────────────────────────────────────────────────────

export interface Conflict {
  task_id: string
  local_agent: string
  remote_agent: string | null
  local_result: string
  remote_status: string | null
  logged_at: string               // ISO 8601
}

// ── RAG ────────────────────────────────────────────────────────────────────

export interface ContextItem {
  id: string
  source_type: 'task_result' | 'chat_message' | 'decision' | 'code_pattern' | 'standard'
  source_id: string
  content: string
  tags: string[]
  similarity_score?: number       // 0–1, populated by pgvector search
  created_at: string              // ISO 8601
}

export interface RAGSearchRequest {
  query: string
  top_k?: number                  // default 5
}

export interface RetrievalLog {
  id: string
  agent_id: string
  query: string
  results_returned: number
  timestamp: string               // ISO 8601
  context_items?: ContextItem[]
}

// ── WebSocket frame types ──────────────────────────────────────────────────
// Mirrors WS_CONTRACTS.md

export type WSMessageType =
  | 'auth' | 'connected'
  | 'message' | 'react' | 'unreact'
  | 'typing' | 'ping' | 'pong'
  | 'reaction' | 'thread_reply' | 'presence'
  | 'idea_surfaced' | 'error'

export interface WSFrame {
  type: WSMessageType
}

export interface WSAuthFrame extends WSFrame {
  type: 'auth'
  agent: string
  token: null
}

export interface WSConnectedFrame extends WSFrame {
  type: 'connected'
  room: string
  agent: string
  recent_messages: ChatMessage[]
}

export interface WSSendMessageFrame extends WSFrame {
  type: 'message'
  room: string
  sender: string
  content: string
  message_type?: MessageType
  thread_id?: string | null
}

export interface WSMessageBroadcast extends WSFrame {
  type: 'message'
  room: string
  data: ChatMessage
}

export interface WSReactFrame extends WSFrame {
  type: 'react' | 'unreact'
  room: string
  message_id: string
  reactor: string
  reaction: ReactionEmoji
}

export interface WSReactionUpdate extends WSFrame {
  type: 'reaction'
  room: string
  message_id: string
  reactions: ReactionMap
}

export interface WSTypingFrame extends WSFrame {
  type: 'typing'
  room: string
  agent: string
  is_typing: boolean
}

export interface WSPresenceFrame extends WSFrame {
  type: 'presence'
  agent: string
  status: AgentStatus
  room: string
}

export interface WSIdeaSurfacedFrame extends WSFrame {
  type: 'idea_surfaced'
  idea: Idea
}

export interface WSErrorFrame extends WSFrame {
  type: 'error'
  code: string
  message: string
}

// ── API client helper types ────────────────────────────────────────────────

export interface ApiError {
  detail: string
  status: number
}

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: ApiError }
