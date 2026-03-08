/**
 * HealthAlerts — navbar badge showing active health alerts.
 * TASK 5012: health alerts visible in frontend navbar.
 */
import { useState, useEffect, useCallback } from 'react';
import { Badge, OverlayTrigger, Popover } from 'react-bootstrap';
import { BsHeartPulse } from 'react-icons/bs';
import { fetchHealth } from '@/api/client';
import type { HealthAlert } from '@/types';

export function HealthAlerts() {
  const [alerts, setAlerts] = useState<HealthAlert[]>([]);

  const refresh = useCallback(async () => {
    try {
      const summary = await fetchHealth();
      setAlerts(summary.alerts);
    } catch {
      // silently ignore — don't break the navbar
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 15000);
    return () => clearInterval(interval);
  }, [refresh]);

  const popover = (
    <Popover id="health-popover">
      <Popover.Header>Health Alerts</Popover.Header>
      <Popover.Body className="p-2" style={{ maxWidth: 320 }}>
        {alerts.length === 0 ? (
          <span className="text-muted small">All agents healthy</span>
        ) : (
          alerts.map((a, i) => (
            <div key={i} className="mb-2 small">
              <Badge bg={a.level === 'critical' ? 'danger' : 'warning'} className="me-1">
                {a.level}
              </Badge>
              <strong>{a.agent}</strong> — {a.reason}
              <div className="text-muted" style={{ fontSize: '0.75em' }}>{a.timestamp.slice(0, 19)}</div>
            </div>
          ))
        )}
      </Popover.Body>
    </Popover>
  );

  return (
    <OverlayTrigger trigger="click" placement="bottom" overlay={popover} rootClose>
      <span
        role="button"
        className="d-flex align-items-center gap-1 text-white"
        style={{ cursor: 'pointer', opacity: alerts.length > 0 ? 1 : 0.6 }}
        title="Agent health alerts"
      >
        <BsHeartPulse />
        {alerts.length > 0 && (
          <Badge bg="danger" pill>{alerts.length}</Badge>
        )}
      </span>
    </OverlayTrigger>
  );
}
