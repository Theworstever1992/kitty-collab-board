"""
token_manager_agent.py — Token Manager Agent (stub).
Reads token_usage_log (TokenUsage table via API), posts weekly report to #manager channel.
Designed to run as a persistent process; call run_once() from tests or orchestrator.
"""

import asyncio

import httpx


class TokenManagerAgent:
    """Polls the governance token-report endpoint and posts summaries to the manager channel."""

    def __init__(self, api_base: str, agent_name: str = "token-manager") -> None:
        self.api_base = api_base.rstrip("/")
        self.agent_name = agent_name

    async def run_once(self) -> dict:
        """
        Fetch GET /api/v2/governance/token-report, format a summary of the top agents
        by cost, post it to POST /api/v2/chat/manager, and return metadata.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch per-agent token totals
            resp = await client.get(f"{self.api_base}/api/v2/governance/token-report")
            resp.raise_for_status()
            report: list[dict] = resp.json()

        # Sort by total_cost_usd descending
        sorted_report = sorted(report, key=lambda x: x.get("total_cost_usd", 0.0), reverse=True)

        # Build summary string
        if sorted_report:
            lines = ["**Weekly Token Usage Report** (top agents by cost):"]
            for entry in sorted_report:
                lines.append(
                    f"  - {entry['agent']}: "
                    f"${entry['total_cost_usd']:.4f} USD | "
                    f"in={entry['total_input']:,} out={entry['total_output']:,} | "
                    f"{entry['request_count']} request(s)"
                )
            summary = "\n".join(lines)
        else:
            summary = "**Weekly Token Usage Report**: No token usage recorded yet."

        # Post summary to #manager channel
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{self.api_base}/api/v2/chat/manager",
                json={
                    "sender": self.agent_name,
                    "content": summary,
                    "type": "update",
                },
            )

        return {"agents_reported": len(sorted_report), "posted": True}

    async def run_loop(self, interval_hours: float = 168.0) -> None:
        """Calls run_once() every interval_hours (default: 168h = 1 week) in a loop."""
        while True:
            await self.run_once()
            await asyncio.sleep(interval_hours * 3600)
