/**
 * TaskCard component - displays a single task
 */
import { Card, Badge, Button, Dropdown } from 'react-bootstrap';
import { 
  BsClock, 
  BsCheckCircle, 
  BsXCircle, 
  BsPauseCircle,
  BsTrash,
  BsPencil,
  BsPerson
} from 'react-icons/bs';
import type { Task, TaskStatus, TaskPriority } from '@/types';

interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
  onStatusChange: (taskId: string, status: TaskStatus) => void;
}

const statusConfig: Record<TaskStatus, { icon: React.ReactNode; variant: string; label: string }> = {
  pending: { icon: <BsClock />, variant: 'warning', label: 'Pending' },
  in_progress: { icon: <BsPauseCircle />, variant: 'info', label: 'In Progress' },
  done: { icon: <BsCheckCircle />, variant: 'success', label: 'Done' },
  blocked: { icon: <BsXCircle />, variant: 'danger', label: 'Blocked' },
};

const priorityConfig: Record<TaskPriority, { variant: string; emoji: string; label: string }> = {
  critical: { variant: 'danger', emoji: '🔴', label: 'Critical' },
  high: { variant: 'warning', emoji: '🟠', label: 'High' },
  normal: { variant: 'secondary', emoji: '⚪', label: 'Normal' },
  low: { variant: 'info', emoji: '🔵', label: 'Low' },
};

const roleColors: Record<string, string> = {
  reasoning: 'primary',
  code: 'success',
  research: 'info',
  summarization: 'warning',
  general: 'secondary',
};

export function TaskCard({ task, onEdit, onDelete, onStatusChange }: TaskCardProps) {
  const status = statusConfig[task.status];
  const priority = priorityConfig[task.priority];

  return (
    <Card className="mb-3 shadow-sm">
      <Card.Body>
        <div className="d-flex justify-content-between align-items-start mb-2">
          <div className="d-flex align-items-center gap-2">
            <span title={priority.label}>{priority.emoji}</span>
            <Card.Title className="mb-0 fs-6">{task.title}</Card.Title>
          </div>
          <Dropdown>
            <Dropdown.Toggle variant="link" size="sm" className="p-0">
              ⋮
            </Dropdown.Toggle>
            <Dropdown.Menu>
              <Dropdown.Item onClick={() => onEdit(task)}>
                <BsPencil className="me-2" /> Edit
              </Dropdown.Item>
              <Dropdown.Divider />
              <Dropdown.Item onClick={() => onDelete(task.id)} className="text-danger">
                <BsTrash className="me-2" /> Delete
              </Dropdown.Item>
            </Dropdown.Menu>
          </Dropdown>
        </div>

        <Card.Text className="text-muted small mb-3">
          {task.description || 'No description'}
        </Card.Text>

        <div className="d-flex flex-wrap gap-2 mb-3">
          <Badge bg={status.variant} className="d-flex align-items-center gap-1">
            {status.icon} {status.label}
          </Badge>
          {task.role && (
            <Badge bg={roleColors[task.role] || 'secondary'}>
              {task.role}
            </Badge>
          )}
          {task.claimed_by && (
            <Badge bg="dark" className="d-flex align-items-center gap-1">
              <BsPerson /> {task.claimed_by}
            </Badge>
          )}
        </div>

        <div className="d-flex gap-2">
          {task.status !== 'pending' && (
            <Button 
              size="sm" 
              variant="outline-warning"
              onClick={() => onStatusChange(task.id, 'pending')}
            >
              <BsClock /> Pending
            </Button>
          )}
          {task.status !== 'in_progress' && (
            <Button 
              size="sm" 
              variant="outline-info"
              onClick={() => onStatusChange(task.id, 'in_progress')}
            >
              <BsPauseCircle /> Start
            </Button>
          )}
          {task.status !== 'done' && (
            <Button 
              size="sm" 
              variant="outline-success"
              onClick={() => onStatusChange(task.id, 'done')}
            >
              <BsCheckCircle /> Done
            </Button>
          )}
          {task.status !== 'blocked' && (
            <Button 
              size="sm" 
              variant="outline-danger"
              onClick={() => onStatusChange(task.id, 'blocked')}
            >
              <BsXCircle /> Block
            </Button>
          )}
        </div>
      </Card.Body>
    </Card>
  );
}
