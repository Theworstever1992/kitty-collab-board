"""
metrics.py — Performance and completion metrics (TASK 6031-6034)

Tracks task completion, agent performance, and system health metrics.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class MetricsCollector:
    """Collects and manages performance metrics."""

    def __init__(self, board_dir: Optional[Path] = None):
        self.board_dir = Path(board_dir) if board_dir else Path(
            os.environ.get("CLOWDER_BOARD_DIR", Path.cwd() / "board")
        )
        self.metrics_file = self.board_dir / "metrics.json"

    def _load_metrics(self) -> Dict:
        """Load existing metrics."""
        if not self.metrics_file.exists():
            return {
                "tasks": {
                    "total_completed": 0,
                    "total_pending": 0,
                    "total_in_progress": 0,
                    "avg_completion_time_seconds": 0,
                    "completion_by_role": {},
                    "completion_rate_percent": 0,
                },
                "agents": {},
                "last_updated": None,
            }

        try:
            return json.loads(self.metrics_file.read_text())
        except Exception:
            return self._load_metrics()

    def _save_metrics(self, metrics: Dict):
        """Save metrics."""
        try:
            self.metrics_file.write_text(json.dumps(metrics, indent=2))
        except Exception:
            pass

    def record_task_completion(self, task_id: str, task: Dict, completion_time_seconds: float):
        """Record a task completion."""
        metrics = self._load_metrics()

        metrics["tasks"]["total_completed"] = metrics["tasks"].get("total_completed", 0) + 1

        # Track by role
        role = task.get("role", "general")
        if role not in metrics["tasks"]["completion_by_role"]:
            metrics["tasks"]["completion_by_role"][role] = 0
        metrics["tasks"]["completion_by_role"][role] += 1

        metrics["last_updated"] = datetime.now().isoformat()
        self._save_metrics(metrics)

    def record_agent_performance(self, agent_name: str, task_id: str, success: bool, duration_seconds: float):
        """Record agent performance."""
        metrics = self._load_metrics()

        if agent_name not in metrics["agents"]:
            metrics["agents"][agent_name] = {
                "tasks_claimed": 0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "success_rate_percent": 0,
                "first_seen": datetime.now().isoformat(),
            }

        agent_metrics = metrics["agents"][agent_name]
        agent_metrics["tasks_claimed"] += 1

        if success:
            agent_metrics["tasks_completed"] += 1
        else:
            agent_metrics["tasks_failed"] += 1

        # Update success rate
        total = agent_metrics["tasks_completed"] + agent_metrics["tasks_failed"]
        agent_metrics["success_rate_percent"] = round(100 * agent_metrics["tasks_completed"] / total, 1) if total > 0 else 0

        agent_metrics["last_task"] = {
            "id": task_id,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }

        metrics["last_updated"] = datetime.now().isoformat()
        self._save_metrics(metrics)

    def get_metrics_summary(self) -> Dict:
        """Get summary of all metrics."""
        metrics = self._load_metrics()
        return metrics

    def get_agent_metrics(self, agent_name: str) -> Optional[Dict]:
        """Get metrics for a specific agent."""
        metrics = self._load_metrics()
        return metrics.get("agents", {}).get(agent_name)

    def get_top_agents(self, limit: int = 5) -> List[tuple]:
        """Get top agents by completion count."""
        metrics = self._load_metrics()
        agents = metrics.get("agents", {})

        sorted_agents = sorted(
            agents.items(),
            key=lambda x: x[1].get("tasks_completed", 0),
            reverse=True
        )

        return sorted_agents[:limit]


# Global metrics instance
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
