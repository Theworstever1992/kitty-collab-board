import type { Agent, Channel, ChatMessage, Task, Idea, TokenBudget, ApiResult } from '../types'

const BASE = '/api'

async function get<T>(path: string): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${BASE}${path}`)
    if (!res.ok) return { ok: false, error: { detail: await res.text(), status: res.status } }
    return { ok: true, data: await res.json() }
  } catch (e) {
    return { ok: false, error: { detail: String(e), status: 0 } }
  }
}

async function post<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) return { ok: false, error: { detail: await res.text(), status: res.status } }
    return { ok: true, data: await res.json() }
  } catch (e) {
    return { ok: false, error: { detail: String(e), status: 0 } }
  }
}

async function patch<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: 'PATCH',
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) return { ok: false, error: { detail: await res.text(), status: res.status } }
    return { ok: true, data: await res.json() }
  } catch (e) {
    return { ok: false, error: { detail: String(e), status: 0 } }
  }
}

export const api = {
  // Agents
  getAgents: () => get<Agent[]>('/v2/agents'),
  getAgent: (name: string) => get<Agent>(`/v2/agents/${name}/profile`),

  // Channels
  getChannels: () => get<Channel[]>('/v2/channels'),
  getMessages: (channel: string, limit = 50) =>
    get<ChatMessage[]>(`/v2/chat/${channel}?limit=${limit}`),

  // Tasks
  getTasks: (teamId?: string) =>
    get<Task[]>(`/v2/tasks${teamId ? `?team_id=${teamId}` : ''}`),
  claimTask: (id: string, agentName: string) =>
    post<{ claimed: boolean }>(`/v2/tasks/${id}/claim`, {
      agent_name: agentName,
      claimed_at: new Date().toISOString(),
    }),
  completeTask: (id: string, agentName: string, result: string) =>
    post<{ ok: boolean }>(`/v2/tasks/${id}/complete`, {
      agent_name: agentName,
      result,
      completed_at: new Date().toISOString(),
    }),

  // Ideas
  getIdeas: () => get<Idea[]>('/v2/ideas'),
  voteIdea: (id: string, voter: string) =>
    post<{ ok: boolean }>(`/v2/ideas/${id}/vote`, { voter }),
  approveIdea: (id: string) =>
    patch<{ ok: boolean }>(`/v2/ideas/${id}/status`, { status: 'approved' }),
  rejectIdea: (id: string) =>
    patch<{ ok: boolean }>(`/v2/ideas/${id}/status`, { status: 'rejected' }),

  // Tokens
  getBudget: (agent: string) => get<TokenBudget>(`/v2/tokens/${agent}/budget`),
  getTokenReport: () => get<TokenBudget[]>('/v2/governance/token-report'),

  // Governance
  getViolations: (agentId?: string) =>
    get<any[]>(`/v2/governance/violations${agentId ? `?agent_id=${agentId}` : ''}`),

  // Agent profiles
  updateProfile: (name: string, payload: unknown) =>
    patch<Agent>(`/v2/agents/${name}/profile`, payload),
  updateAvatar: (name: string, svgText: string) =>
    patch<Agent>(`/v2/agents/${name}/avatar`, { avatar_svg: svgText }),
}
