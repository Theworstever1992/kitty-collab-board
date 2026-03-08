/**
 * AnalyticsDashboard.tsx — Kitty Collab Board
 * Analytics dashboard showing task metrics, agent performance, and trends.
 * TASK 6033 — Analytics Dashboard (React)
 */

import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

interface AnalyticsSummary {
  timestamp: string;
  total_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  done_tasks: number;
  blocked_tasks: number;
  total_agents: number;
  online_agents: number;
  avg_completion_time_seconds: number;
  tasks_completed_today: number;
  tasks_completed_this_week: number;
  tasks_completed_this_month: number;
}

interface AgentMetrics {
  agent_name: string;
  tasks_claimed: number;
  tasks_completed: number;
  tasks_blocked: number;
  success_rate: number;
  total_execution_time_seconds: number;
  avg_execution_time_seconds: number;
}

interface TrendPoint {
  date: string;
  completed: number;
}

export const AnalyticsDashboard: React.FC = () => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [agents, setAgents] = useState<AgentMetrics[]>([]);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trendDays, setTrendDays] = useState(7);

  useEffect(() => {
    loadAnalytics();
  }, [trendDays]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [summaryRes, agentsRes, trendRes] = await Promise.all([
        api.get('/api/analytics/summary'),
        api.get('/api/analytics/agents'),
        api.get(`/api/analytics/completion-trend?days=${trendDays}`),
      ]);

      setSummary(summaryRes.data);
      setAgents(agentsRes.data.agents || []);
      setTrend(trendRes.data.trend || []);
      setError(null);
    } catch (err) {
      setError('Failed to load analytics data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  const formatNumber = (num: number): string => {
    return num.toLocaleString();
  };

  if (loading) {
    return (
      <div className="analytics-dashboard loading">
        <div className="spinner">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-dashboard error">
        <p className="error-message">{error}</p>
        <button onClick={loadAnalytics}>Retry</button>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h2>📊 Analytics Dashboard</h2>
        <button onClick={loadAnalytics} className="refresh-btn">↻ Refresh</button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="summary-cards">
          <div className="summary-card total">
            <h3>Total Tasks</h3>
            <p className="value">{formatNumber(summary.total_tasks)}</p>
          </div>
          <div className="summary-card pending">
            <h3>Pending</h3>
            <p className="value">{formatNumber(summary.pending_tasks)}</p>
          </div>
          <div className="summary-card in-progress">
            <h3>In Progress</h3>
            <p className="value">{formatNumber(summary.in_progress_tasks)}</p>
          </div>
          <div className="summary-card done">
            <h3>Completed</h3>
            <p className="value">{formatNumber(summary.done_tasks)}</p>
          </div>
          <div className="summary-card blocked">
            <h3>Blocked</h3>
            <p className="value">{formatNumber(summary.blocked_tasks)}</p>
          </div>
          <div className="summary-card agents">
            <h3>Agents Online</h3>
            <p className="value">{summary.online_agents} / {summary.total_agents}</p>
          </div>
          <div className="summary-card avg-time">
            <h3>Avg Completion</h3>
            <p className="value">{formatTime(summary.avg_completion_time_seconds)}</p>
          </div>
        </div>
      )}

      {/* Completion Stats */}
      {summary && (
        <div className="completion-stats">
          <h3>Completion Statistics</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="label">Today</span>
              <span className="value">{formatNumber(summary.tasks_completed_today)}</span>
            </div>
            <div className="stat-item">
              <span className="label">This Week</span>
              <span className="value">{formatNumber(summary.tasks_completed_this_week)}</span>
            </div>
            <div className="stat-item">
              <span className="label">This Month</span>
              <span className="value">{formatNumber(summary.tasks_completed_this_month)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Completion Trend Chart */}
      <div className="trend-section">
        <div className="trend-header">
          <h3>Completion Trend</h3>
          <div className="trend-controls">
            <button 
              className={trendDays === 7 ? 'active' : ''} 
              onClick={() => setTrendDays(7)}
            >
              7D
            </button>
            <button 
              className={trendDays === 14 ? 'active' : ''} 
              onClick={() => setTrendDays(14)}
            >
              14D
            </button>
            <button 
              className={trendDays === 30 ? 'active' : ''} 
              onClick={() => setTrendDays(30)}
            >
              30D
            </button>
          </div>
        </div>
        <div className="trend-chart">
          {trend.length === 0 ? (
            <p className="no-data">No completion data available</p>
          ) : (
            <div className="bar-chart">
              {trend.map((point) => (
                <div key={point.date} className="bar-container">
                  <div 
                    className="bar" 
                    style={{ height: `${Math.max(point.completed * 10, 2)}px` }}
                    title={`${point.date}: ${point.completed} tasks`}
                  />
                  <span className="bar-label">{point.date.slice(5)}</span>
                  <span className="bar-value">{point.completed}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Agent Performance Table */}
      <div className="agent-performance">
        <h3>Agent Performance</h3>
        {agents.length === 0 ? (
          <p className="no-data">No agent metrics available</p>
        ) : (
          <table className="agent-table">
            <thead>
              <tr>
                <th>Agent</th>
                <th>Claimed</th>
                <th>Completed</th>
                <th>Blocked</th>
                <th>Success Rate</th>
                <th>Avg Time</th>
              </tr>
            </thead>
            <tbody>
              {agents
                .sort((a, b) => b.tasks_completed - a.tasks_completed)
                .map((agent) => (
                  <tr key={agent.agent_name}>
                    <td className="agent-name">{agent.agent_name}</td>
                    <td>{formatNumber(agent.tasks_claimed)}</td>
                    <td>{formatNumber(agent.tasks_completed)}</td>
                    <td>{formatNumber(agent.tasks_blocked)}</td>
                    <td>
                      <span className={`success-rate ${agent.success_rate >= 0.8 ? 'high' : agent.success_rate >= 0.5 ? 'medium' : 'low'}`}>
                        {(agent.success_rate * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td>{formatTime(agent.avg_execution_time_seconds)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Export Options */}
      <div className="export-section">
        <h3>Export Data</h3>
        <div className="export-buttons">
          <a href="/api/analytics/export/csv" className="export-btn csv">
            📥 Export CSV
          </a>
          <a href="/api/analytics/export/json" className="export-btn json">
            📥 Export JSON
          </a>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
