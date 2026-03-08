/**
 * TaskBoard component - main task dashboard
 */
import { useState, useEffect, useCallback } from 'react';
import { Container, Row, Col, Button, Spinner, Alert, Form } from 'react-bootstrap';
import { BsPlus, BsArrowClockwise } from 'react-icons/bs';
import { TaskCard } from './TaskCard';
import { TaskModal } from './TaskModal';
import { fetchTasks, deleteTask, updateTask, createTask } from '@/api/client';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { Task, TaskStatus, TaskCreateRequest } from '@/types';

export function TaskBoard() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<TaskStatus | 'all'>('all');
  const [showModal, setShowModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  const loadTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const status = filterStatus === 'all' ? undefined : filterStatus;
      const { tasks } = await fetchTasks(status);
      setTasks(tasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  }, [filterStatus]);

  const handleBoardUpdate = useCallback((data: { tasks: Task[] }) => {
    if (filterStatus === 'all') {
      setTasks(data.tasks);
    } else {
      setTasks(data.tasks.filter(t => t.status === filterStatus));
    }
  }, [filterStatus]);

  const { isConnected } = useWebSocket('ws://localhost:8000/api/ws/board', {
    onBoardUpdate: handleBoardUpdate,
  });

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const handleDelete = async (taskId: string) => {
    if (!confirm('Delete this task?')) return;
    try {
      await deleteTask(taskId);
      setTasks(prev => prev.filter(t => t.id !== taskId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete task');
    }
  };

  const handleStatusChange = async (taskId: string, status: TaskStatus) => {
    try {
      await updateTask(taskId, { status });
      setTasks(prev => prev.map(t => 
        t.id === taskId ? { ...t, status } : t
      ));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update task');
    }
  };

  const handleSave = async (taskData: TaskCreateRequest) => {
    try {
      if (editingTask) {
        await updateTask(editingTask.id, taskData);
        setTasks(prev => prev.map(t => 
          t.id === editingTask.id ? { ...t, ...taskData } : t
        ));
      } else {
        const newTask = await createTask(taskData);
        setTasks(prev => [...prev, newTask]);
      }
      setShowModal(false);
      setEditingTask(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save task');
    }
  };

  const handleEdit = (task: Task) => {
    setEditingTask(task);
    setShowModal(true);
  };

  const handleAdd = () => {
    setEditingTask(null);
    setShowModal(true);
  };

  const statusCounts = {
    all: tasks.length,
    pending: tasks.filter(t => t.status === 'pending').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
    done: tasks.filter(t => t.status === 'done').length,
    blocked: tasks.filter(t => t.status === 'blocked').length,
  };

  return (
    <Container className="py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2>📋 Task Board</h2>
          <small className="text-muted">
            {isConnected ? '🟢 Live' : '🔴 Disconnected'} | {tasks.length} tasks
          </small>
        </div>
        <div className="d-flex gap-2">
          <Button variant="outline-secondary" onClick={loadTasks}>
            <BsArrowClockwise /> Refresh
          </Button>
          <Button variant="primary" onClick={handleAdd}>
            <BsPlus /> Add Task
          </Button>
        </div>
      </div>

      <Form.Select 
        className="mb-4 w-auto"
        value={filterStatus}
        onChange={(e) => setFilterStatus(e.target.value as TaskStatus | 'all')}
      >
        <option value="all">All Tasks ({statusCounts.all})</option>
        <option value="pending">⏳ Pending ({statusCounts.pending})</option>
        <option value="in_progress">🔄 In Progress ({statusCounts.in_progress})</option>
        <option value="done">✅ Done ({statusCounts.done})</option>
        <option value="blocked">🚫 Blocked ({statusCounts.blocked})</option>
      </Form.Select>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <div className="text-center py-5">
          <Spinner animation="border" />
        </div>
      ) : tasks.length === 0 ? (
        <Alert variant="info">
          No tasks found. Create your first task to get started!
        </Alert>
      ) : (
        <Row>
          {tasks.map(task => (
            <Col key={task.id} md={6} lg={4}>
              <TaskCard
                task={task}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onStatusChange={handleStatusChange}
              />
            </Col>
          ))}
        </Row>
      )}

      <TaskModal
        show={showModal}
        onHide={() => {
          setShowModal(false);
          setEditingTask(null);
        }}
        task={editingTask}
        onSave={handleSave}
      />
    </Container>
  );
}
