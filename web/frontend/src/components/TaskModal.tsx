/**
 * TaskModal component - add/edit task form
 */
import { useState, useEffect } from 'react';
import { Modal, Form, Button } from 'react-bootstrap';
import type { Task, TaskCreateRequest, TaskPriority, AgentRole } from '@/types';

interface TaskModalProps {
  show: boolean;
  onHide: () => void;
  task: Task | null;
  onSave: (task: TaskCreateRequest) => void;
}

const priorities: { value: TaskPriority; label: string; emoji: string }[] = [
  { value: 'critical', label: 'Critical', emoji: '🔴' },
  { value: 'high', label: 'High', emoji: '🟠' },
  { value: 'normal', label: 'Normal', emoji: '⚪' },
  { value: 'low', label: 'Low', emoji: '🔵' },
];

const roles: { value: AgentRole; label: string }[] = [
  { value: 'reasoning', label: 'Reasoning' },
  { value: 'code', label: 'Code' },
  { value: 'research', label: 'Research' },
  { value: 'summarization', label: 'Summarization' },
  { value: 'general', label: 'General' },
];

export function TaskModal({ show, onHide, task, onSave }: TaskModalProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<TaskPriority>('normal');
  const [role, setRole] = useState<AgentRole | undefined>(undefined);

  const isEditing = !!task;

  useEffect(() => {
    if (task) {
      setTitle(task.title);
      setDescription(task.description);
      setPriority(task.priority);
      setRole(task.role);
    } else {
      setTitle('');
      setDescription('');
      setPriority('normal');
      setRole(undefined);
    }
  }, [task, show]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      title,
      description,
      prompt: description,
      priority,
      role,
    });
  };

  return (
    <Modal show={show} onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>{isEditing ? 'Edit Task' : 'New Task'}</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit}>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Title</Form.Label>
            <Form.Control
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Task title"
              required
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Task description (also used as prompt for agents)"
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Priority</Form.Label>
            <Form.Select
              value={priority}
              onChange={(e) => setPriority(e.target.value as TaskPriority)}
            >
              {priorities.map(p => (
                <option key={p.value} value={p.value}>
                  {p.emoji} {p.label}
                </option>
              ))}
            </Form.Select>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Role (Optional)</Form.Label>
            <Form.Select
              value={role || ''}
              onChange={(e) => setRole(e.target.value as AgentRole || undefined)}
            >
              <option value="">Auto-assign</option>
              {roles.map(r => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </Form.Select>
            <Form.Text className="text-muted">
              Specific role for this task. Leave empty for auto-assignment.
            </Form.Text>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button variant="primary" type="submit">
            {isEditing ? 'Save Changes' : 'Create Task'}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
