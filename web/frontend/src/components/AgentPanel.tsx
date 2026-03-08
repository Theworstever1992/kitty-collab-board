/**
 * AgentPanel — displays agent health status using /api/health thresholds.
 * TASK 5011: uses 60s/300s thresholds instead of binary online/offline.
 */
import { useState, useEffect, useCallback } from 'react';
import { Card, Badge, Spinner, Alert, Row, Col } from 'react-bootstrap';
import { BsCpu } from 'react-icons/bs';
import { fetchHealth } from '@/api/client';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { AgentHealth, HealthStatus } from '@/types';

const roleColors: Record<string, string> = {
  reasoning: 'primary',
  code: 'success',
  research: 'info',
  summarization: 'warning',
  general: 'secondary',
};

function healthBadgeVariant(status: HealthStatus): string {
  return { online: 'success', warning: 'warning', offline: 'danger', unknown: 'secondary' }[status] ?? 'secondary';
}

function healthLabel(status: HealthStatus, seconds: number | null): string {
  if (status === 'online') return 'online';
  if (status === 'warning') return `warn ${Math.round(seconds ?? 0)}s`;
  if (status === 'offline') return `offline ${Math.round(seconds ?? 0)}s`;
  return 'unknown';
}

export function AgentPanel() {
  const [agents, setAgents] = useState<AgentHealth[]>([]);
  const [alertCount, setAlertCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadHealth = useCallback(async () => {
    try {
      setError(null);
      const summary = await fetchHealth();
      setAgents(summary.agents);
      setAlertCount(summary.alerts.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load health');
    } finally {
      setLoading(false);
    }
  }, []);

  // Re-check health whenever board updates (agents heartbeat via board cycle)
  const { isConnected } = useWebSocket('ws://localhost:8000/api/ws/board', {
    onBoardUpdate: loadHealth,
  });

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 10000);
    return () => clearInterval(interval);
  }, [loadHealth]);

  const onlineCount = agents.filter(a => a.status === 'online').length;

  return (
    <Card className="mb-3">
      <Card.Header className="d-flex justify-content-between align-items-center">
        <div className="d-flex align-items-center gap-2">
          <BsCpu />
          <strong>Agents</strong>
          {isConnected && <Badge bg="success" className="ms-2">Live</Badge>}
          {alertCount > 0 && (
            <Badge bg="danger" className="ms-1" title={`${alertCount} health alert(s)`}>
              {alertCount} alert{alertCount > 1 ? 's' : ''}
            </Badge>
          )}
        </div>
        <div className="small text-muted">{onlineCount}/{agents.length} online</div>
      </Card.Header>
      <Card.Body>
        {error && <Alert variant="danger" className="py-2">{error}</Alert>}

        {loading && agents.length === 0 ? (
          <div className="text-center py-3"><Spinner animation="border" size="sm" /></div>
        ) : agents.length === 0 ? (
          <Alert variant="info" className="py-2">No agents registered.</Alert>
        ) : (
          <Row className="g-2">
            {agents.map(agent => (
              <Col key={agent.name} xs={12}>
                <div className="d-flex align-items-center justify-content-between p-2 border rounded">
                  <div>
                    <div className="fw-bold">🤖 {agent.name}</div>
                    <small className="text-muted">{agent.model}</small>
                  </div>
                  <div className="d-flex align-items-center gap-2">
                    {agent.role && (
                      <Badge bg={roleColors[agent.role] ?? 'secondary'}>{agent.role}</Badge>
                    )}
                    <Badge bg={healthBadgeVariant(agent.status)}>
                      {healthLabel(agent.status, agent.seconds_since)}
                    </Badge>
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        )}
      </Card.Body>
    </Card>
  );
}
