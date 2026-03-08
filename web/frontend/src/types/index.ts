/**
 * TypeScript types for Kitty Collab Board
 */

export type TaskStatus = 'pending' | 'in_progress' | 'done' | 'blocked';
export type TaskPriority = 'critical' | 'high' | 'normal' | 'low';
export type AgentRole = 'reasoning' | 'code' | 'research' | 'summarization' | 'general';

export interface Task {
  id: string;
  title: string;
  description: string;
  prompt?: string;
  status: TaskStatus;
  created_at: string;
  claimed_by: string | null;
  claimed_at?: string;
  completed_by?: string;
  completed_at?: string;
  result?: string;
  role?: AgentRole;
  priority: TaskPriority;
  priority_order: number;
  blocked_by?: string;
  blocked_at?: string;
  block_reason?: string;
}

export interface Agent {
  name: string;
  model: string;
  provider: string;
  role: AgentRole;
  status: 'online' | 'offline' | 'busy';
  last_seen?: string;
  current_task?: string;
}

export interface BoardState {
  tasks: Task[];
}

export interface WebSocketMessage {
  type: 'board_update' | 'log' | 'ping';
  data?: BoardState;
  message?: string;
}

export interface TaskCreateRequest {
  title: string;
  description?: string;
  prompt?: string;
  role?: AgentRole;
  priority?: TaskPriority;
}

export interface TaskUpdateRequest {
  title?: string;
  description?: string;
  prompt?: string;
  role?: AgentRole;
  priority?: TaskPriority;
  status?: TaskStatus;
}

export type HealthStatus = 'online' | 'warning' | 'offline' | 'unknown';

export interface AgentHealth {
  name: string;
  status: HealthStatus;
  last_seen: string | null;
  seconds_since: number | null;
  model?: string;
  role?: string;
}

export interface HealthAlert {
  agent: string;
  level: 'warning' | 'critical';
  reason: string;
  timestamp: string;
}

export interface HealthSummary {
  checked_at: string;
  agents: AgentHealth[];
  alerts: HealthAlert[];
  counts: { online: number; warning: number; offline: number; total: number };
}
