"""
context_manager.py — Kitty Collab Board
Context and Token Manager for the Kitty Collab Protocol.

Tracks token consumption, USD costs, and budget limits per agent/team.
Parses [TOKENS: input=X output=Y] markers from messages.
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from agents.atomic import atomic_write, atomic_read


BOARD_DIR = Path(
    os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent.parent / "board")
)
CONTEXT_METRICS_FILE = BOARD_DIR / ".context_metrics.json"
BUDGET_FILE = BOARD_DIR / ".token_budget.json"


# Token-to-USD conversion rates (approximate, varies by provider)
TOKEN_RATES = {
    # Anthropic Claude
    "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},  # per 1M tokens
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    
    # Alibaba Qwen (DashScope)
    "qwen-plus": {"input": 0.4, "output": 1.2},  # per 1K tokens, scaled to 1M
    "qwen-max": {"input": 1.2, "output": 3.6},
    
    # Google Gemini
    "gemini-pro": {"input": 0.5, "output": 1.5},
    "gemini-ultra": {"input": 7.0, "output": 21.0},
    
    # OpenAI
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    
    # Ollama (local, free)
    "llama3": {"input": 0.0, "output": 0.0},
    "llama3.2": {"input": 0.0, "output": 0.0},
    "codellama": {"input": 0.0, "output": 0.0},
    "mistral": {"input": 0.0, "output": 0.0},
}

# Default rate if model not found (conservative estimate)
DEFAULT_RATE = {"input": 1.0, "output": 3.0}


class ContextManager:
    """
    Tracks token usage and costs across the Kitty Collab Board.
    """
    
    def __init__(self):
        self.metrics_file = CONTEXT_METRICS_FILE
        self.budget_file = BUDGET_FILE
    
    def log_token_usage(
        self,
        agent: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "unknown",
        message_id: Optional[str] = None,
    ) -> dict:
        """
        Log token usage for an agent.
        
        Args:
            agent: Agent name (e.g., "claude-code", "qwen-analyst")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name for rate lookup
            message_id: Optional message ID reference
            
        Returns:
            Usage record with cost
        """
        # Calculate cost
        rate = self._get_rate_for_model(model)
        input_cost = (input_tokens / 1_000_000) * rate["input"]
        output_cost = (output_tokens / 1_000_000) * rate["output"]
        total_cost = input_cost + output_cost
        
        # Load metrics
        metrics = atomic_read(self.metrics_file, {
            "agents": {},
            "total": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
            },
            "sessions": [],
        })
        
        # Update agent metrics
        if agent not in metrics["agents"]:
            metrics["agents"][agent] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "messages": [],
                "models": {},
            }
        
        agent_metrics = metrics["agents"][agent]
        agent_metrics["input_tokens"] += input_tokens
        agent_metrics["output_tokens"] += output_tokens
        agent_metrics["total_tokens"] += input_tokens + output_tokens
        agent_metrics["total_cost_usd"] += total_cost
        
        # Track by model
        if model not in agent_metrics["models"]:
            agent_metrics["models"][model] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "count": 0,
            }
        
        agent_metrics["models"][model]["input_tokens"] += input_tokens
        agent_metrics["models"][model]["output_tokens"] += output_tokens
        agent_metrics["models"][model]["count"] += 1
        
        # Track message
        message_record = {
            "message_id": message_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": total_cost,
            "model": model,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Keep last 1000 messages per agent
        agent_metrics["messages"].append(message_record)
        if len(agent_metrics["messages"]) > 1000:
            agent_metrics["messages"] = agent_metrics["messages"][-1000:]
        
        # Update totals
        metrics["total"]["input_tokens"] += input_tokens
        metrics["total"]["output_tokens"] += output_tokens
        metrics["total"]["total_tokens"] += input_tokens + output_tokens
        metrics["total"]["total_cost_usd"] += total_cost
        
        # Add to session
        current_session = self._get_current_session(metrics)
        if current_session:
            current_session["input_tokens"] += input_tokens
            current_session["output_tokens"] += output_tokens
            current_session["total_tokens"] += input_tokens + output_tokens
            current_session["total_cost_usd"] += total_cost
        
        # Save
        atomic_write(self.metrics_file, metrics)
        
        return {
            "agent": agent,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": total_cost,
            "model": model,
        }
    
    def parse_and_log_tokens(
        self,
        content: str,
        agent: str,
        model: str = "unknown",
        message_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Parse token markers from message content and log usage.
        
        Looks for markers like: [TOKENS: input=1500 output=800]
        
        Args:
            content: Message content to parse
            agent: Agent name
            model: Model name
            message_id: Optional message ID
            
        Returns:
            Usage record if tokens found, None otherwise
        """
        # Pattern: [TOKENS: input=1500 output=800]
        pattern = r'\[TOKENS:\s*input=(\d+)\s+output=(\d+)\]'
        match = re.search(pattern, content, re.IGNORECASE)
        
        if not match:
            return None
        
        input_tokens = int(match.group(1))
        output_tokens = int(match.group(2))
        
        return self.log_token_usage(
            agent=agent,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            message_id=message_id,
        )
    
    def set_budget(
        self,
        agent: Optional[str] = None,
        team: Optional[str] = None,
        daily_limit: float = 0.0,
        monthly_limit: float = 0.0,
    ) -> dict:
        """
        Set token budget for an agent or team.
        
        Args:
            agent: Agent name (mutually exclusive with team)
            team: Team name (mutually exclusive with agent)
            daily_limit: Daily USD limit (0 = unlimited)
            monthly_limit: Monthly USD limit (0 = unlimited)
            
        Returns:
            Budget record
        """
        if agent and team:
            raise ValueError("Specify either agent or team, not both")
        if not agent and not team:
            raise ValueError("Specify either agent or team")
        
        budgets = atomic_read(self.budget_file, {"budgets": {}})
        
        key = f"agent:{agent}" if agent else f"team:{team}"
        
        budget = {
            "key": key,
            "agent": agent,
            "team": team,
            "daily_limit_usd": daily_limit,
            "monthly_limit_usd": monthly_limit,
            "updated_at": datetime.now().isoformat(),
        }
        
        budgets["budgets"][key] = budget
        atomic_write(self.budget_file, budgets)
        
        return budget
    
    def check_budget(self, agent: str) -> dict:
        """
        Check if an agent has budget remaining.
        
        Args:
            agent: Agent name
            
        Returns:
            Budget status dict
        """
        budgets = atomic_read(self.budget_file, {"budgets": {}})
        metrics = atomic_read(self.metrics_file, {"agents": {}, "sessions": []})
        
        result = {
            "agent": agent,
            "has_budget": True,
            "daily_remaining": None,
            "monthly_remaining": None,
            "daily_spent": 0.0,
            "monthly_spent": 0.0,
        }
        
        # Get budget for agent
        budget_key = f"agent:{agent}"
        budget = budgets.get("budgets", {}).get(budget_key)
        
        if not budget:
            # No budget set = unlimited
            return result
        
        # Calculate spending
        agent_metrics = metrics.get("agents", {}).get(agent, {})
        
        # Daily spending (last 24 hours)
        day_ago = (datetime.now() - timedelta(days=1)).isoformat()
        daily_messages = [
            m for m in agent_metrics.get("messages", [])
            if m.get("timestamp", "") > day_ago
        ]
        result["daily_spent"] = sum(m.get("cost_usd", 0) for m in daily_messages)
        
        # Monthly spending (last 30 days)
        month_ago = (datetime.now() - timedelta(days=30)).isoformat()
        monthly_messages = [
            m for m in agent_metrics.get("messages", [])
            if m.get("timestamp", "") > month_ago
        ]
        result["monthly_spent"] = sum(m.get("cost_usd", 0) for m in monthly_messages)
        
        # Check limits
        daily_limit = budget.get("daily_limit_usd", 0)
        monthly_limit = budget.get("monthly_limit_usd", 0)
        
        if daily_limit > 0:
            result["daily_remaining"] = daily_limit - result["daily_spent"]
            if result["daily_remaining"] <= 0:
                result["has_budget"] = False
        
        if monthly_limit > 0:
            result["monthly_remaining"] = monthly_limit - result["monthly_spent"]
            if result["monthly_remaining"] <= 0:
                result["has_budget"] = False
        
        return result
    
    def get_usage_report(
        self,
        period: str = "all",
        group_by: str = "agent",
    ) -> dict:
        """
        Get token usage report.
        
        Args:
            period: Time period (all, day, week, month)
            group_by: Grouping (agent, model, team)
            
        Returns:
            Usage report dict
        """
        metrics = atomic_read(self.metrics_file, {"agents": {}, "total": {}})
        
        report = {
            "period": period,
            "group_by": group_by,
            "generated_at": datetime.now().isoformat(),
            "total": metrics.get("total", {}),
            "breakdown": {},
        }
        
        if group_by == "agent":
            report["breakdown"] = metrics.get("agents", {})
        elif group_by == "model":
            # Aggregate by model across all agents
            by_model = {}
            for agent_data in metrics.get("agents", {}).values():
                for model, model_data in agent_data.get("models", {}).items():
                    if model not in by_model:
                        by_model[model] = {
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "count": 0,
                        }
                    by_model[model]["input_tokens"] += model_data.get("input_tokens", 0)
                    by_model[model]["output_tokens"] += model_data.get("output_tokens", 0)
                    by_model[model]["count"] += model_data.get("count", 0)
            report["breakdown"] = by_model
        
        return report
    
    def _get_rate_for_model(self, model: str) -> dict:
        """Get token rate for a model."""
        # Try exact match
        if model in TOKEN_RATES:
            return TOKEN_RATES[model]
        
        # Try partial match
        for key, rate in TOKEN_RATES.items():
            if key in model.lower():
                return rate
        
        return DEFAULT_RATE
    
    def _get_current_session(self, metrics: dict) -> Optional[dict]:
        """Get or create current session."""
        today = datetime.now().date().isoformat()
        
        for session in metrics.get("sessions", []):
            if session.get("date") == today:
                return session
        
        # Create new session
        new_session = {
            "date": today,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
        }
        metrics["sessions"].append(new_session)
        
        return new_session
    
    def reset_session(self) -> dict:
        """Reset the current session."""
        metrics = atomic_read(self.metrics_file, {"sessions": []})
        
        # Archive current session
        today = datetime.now().date().isoformat()
        archived = []
        for session in metrics.get("sessions", []):
            if session.get("date") == today:
                archived.append(session)
        
        metrics["sessions"] = [s for s in metrics["sessions"] if s.get("date") != today]
        atomic_write(self.metrics_file, metrics)
        
        return {
            "archived": archived,
            "reset_at": datetime.now().isoformat(),
        }


# Global context manager instance
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get the global context manager instance."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def log_tokens(
    agent: str,
    input_tokens: int,
    output_tokens: int,
    model: str = "unknown",
) -> dict:
    """Convenience function to log token usage."""
    return get_context_manager().log_token_usage(
        agent=agent,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=model,
    )


def check_budget(agent: str) -> dict:
    """Convenience function to check agent budget."""
    return get_context_manager().check_budget(agent)
