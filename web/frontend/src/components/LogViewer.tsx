/**
 * LogViewer component - displays log stream
 */
import { useState, useEffect, useRef } from 'react';
import { Card, Badge, Form, Button } from 'react-bootstrap';
import { BsTerminal, BsTrash, BsPause, BsPlay } from 'react-icons/bs';
import { useWebSocket } from '@/hooks/useWebSocket';

interface LogEntry {
  id: number;
  timestamp: string;
  message: string;
  type: 'info' | 'warn' | 'error';
}

export function LogViewer() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [filter, setFilter] = useState('');
  const logIdRef = useRef(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleLog = (message: string) => {
    if (isPaused) return;

    const newLog: LogEntry = {
      id: logIdRef.current++,
      timestamp: new Date().toLocaleTimeString(),
      message,
      type: message.includes('ERROR') ? 'error' : 
            message.includes('WARN') ? 'warn' : 'info',
    };

    setLogs(prev => [...prev.slice(-99), newLog]);
  };

  const { isConnected } = useWebSocket('ws://localhost:8000/api/ws/logs', {
    onLog: handleLog,
  });

  // Auto-scroll to bottom
  useEffect(() => {
    if (!isPaused) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isPaused]);

  const clearLogs = () => {
    setLogs([]);
  };

  const filteredLogs = logs.filter(log =>
    log.message.toLowerCase().includes(filter.toLowerCase())
  );

  const getLogColor = (type: LogEntry['type']) => {
    switch (type) {
      case 'error':
        return 'text-danger';
      case 'warn':
        return 'text-warning';
      default:
        return 'text-light';
    }
  };

  return (
    <Card className="mt-4">
      <Card.Header className="d-flex justify-content-between align-items-center">
        <div className="d-flex align-items-center gap-2">
          <BsTerminal />
          <strong>Logs</strong>
          {isConnected && <Badge bg="success">Live</Badge>}
        </div>
        <div className="d-flex gap-2">
          <Button
            variant="outline-light"
            size="sm"
            onClick={() => setIsPaused(!isPaused)}
          >
            {isPaused ? <BsPlay /> : <BsPause />}
          </Button>
          <Button
            variant="outline-danger"
            size="sm"
            onClick={clearLogs}
          >
            <BsTrash />
          </Button>
        </div>
      </Card.Header>
      <Card.Body className="p-0">
        <Form.Control
          type="text"
          placeholder="Filter logs..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="border-0 border-bottom rounded-0"
        />
        <div
          style={{
            height: '200px',
            overflowY: 'auto',
            backgroundColor: '#1e1e1e',
            fontFamily: 'monospace',
            fontSize: '0.85rem',
          }}
          className="p-2"
        >
          {filteredLogs.length === 0 ? (
            <div className="text-muted text-center py-4">
              {logs.length === 0 ? 'No logs yet...' : 'No matching logs'}
            </div>
          ) : (
            filteredLogs.map(log => (
              <div key={log.id} className={`${getLogColor(log.type)} mb-1`}>
                <span className="text-secondary">[{log.timestamp}]</span>{' '}
                {log.message}
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </Card.Body>
    </Card>
  );
}
