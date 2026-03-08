/**
 * API client for Kitty Collab Board backend
 */
import type { Task, TaskCreateRequest, TaskUpdateRequest, Agent, BoardState, HealthSummary } from '@/types';

const API_BASE = '/api';

export async function fetchTasks(status?: string, role?: string): Promise<{ tasks: Task[]; count: number }> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (role) params.append('role', role);
  
  const response = await fetch(`${API_BASE}/tasks?${params}`);
  if (!response.ok) throw new Error('Failed to fetch tasks');
  return response.json();
}

export async function fetchTask(taskId: string): Promise<Task> {
  const response = await fetch(`${API_BASE}/tasks/${taskId}`);
  if (!response.ok) throw new Error('Failed to fetch task');
  return response.json();
}

export async function createTask(task: TaskCreateRequest): Promise<Task> {
  const response = await fetch(`${API_BASE}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task),
  });
  if (!response.ok) throw new Error('Failed to create task');
  return response.json();
}

export async function updateTask(taskId: string, updates: TaskUpdateRequest): Promise<Task> {
  const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!response.ok) throw new Error('Failed to update task');
  return response.json();
}

export async function deleteTask(taskId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete task');
}

export async function fetchAgents(): Promise<{ agents: Record<string, Agent>; count: number }> {
  const response = await fetch(`${API_BASE}/agents`);
  if (!response.ok) throw new Error('Failed to fetch agents');
  return response.json();
}

export async function fetchBoard(): Promise<BoardState> {
  const response = await fetch(`${API_BASE}/board`);
  if (!response.ok) throw new Error('Failed to fetch board');
  return response.json();
}

export async function fetchHealth(): Promise<HealthSummary> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error('Failed to fetch health');
  return response.json();
}
