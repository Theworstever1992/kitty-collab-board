/**
 * App.tsx — Kitty Collab Board Web GUI
 * Main application component
 */
import { Container, Row, Col, Navbar } from 'react-bootstrap';
import { TaskBoard } from '@/components/TaskBoard';
import { AgentPanel } from '@/components/AgentPanel';
import { LogViewer } from '@/components/LogViewer';
import { HealthAlerts } from '@/components/HealthAlerts';
import './App.css';

function App() {
  return (
    <div className="app">
      <Navbar bg="dark" variant="dark" className="mb-4">
        <Container>
          <Navbar.Brand href="#">
            <span className="brand-cat">🐱</span>
            <span className="brand-text">Kitty Collab Board</span>
            <small className="brand-subtitle">codename: CLOWDER</small>
          </Navbar.Brand>
          <div className="ms-auto">
            <HealthAlerts />
          </div>
        </Container>
      </Navbar>

      <Container fluid="lg">
        <Row>
          <Col lg={8}>
            <TaskBoard />
          </Col>
          <Col lg={4}>
            <AgentPanel />
            <LogViewer />
          </Col>
        </Row>
      </Container>

      <footer className="text-center py-4 text-muted">
        <small>
          Kitty Collab Board — Multi-agent AI collaboration system
        </small>
      </footer>
    </div>
  );
}

export default App;
