"""
war_room.py — Kitty Collab Board
War Room workflow for the Kitty Collab Protocol.

Implements the 10-step coordination flow:
1. Kick-off → 2. Assessment → 3. Synthesis → 4. Human Approval → 5. Dispatch
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from agents.channels import Channel, get_or_create_channel, get_channel
from agents.atomic import atomic_write, atomic_read


BOARD_DIR = Path(
    os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent.parent / "board")
)
APPROVALS_FILE = BOARD_DIR / ".approvals.json"


class WarRoom:
    """
    War Room coordinator for multi-agent collaboration.
    
    Facilitates structured brainstorming and human approval workflow.
    """
    
    def __init__(self):
        self.war_room = get_or_create_channel("war-room", "Multi-agent brainstorming and coordination")
        self.approvals = get_or_create_channel("approvals", "Human approval queue for plans")
        self.tasks = get_or_create_channel("tasks", "Dispatched tasks for agents")
    
    def kick_off(self, prompt: str, coordinator: str = "human") -> dict:
        """
        Step 1: Kick-off a new mission.
        
        Posts the initial prompt to the war-room channel to start the coordination flow.
        
        Args:
            prompt: The mission prompt or task description
            coordinator: Who is coordinating (usually "human")
            
        Returns:
            Kick-off message dict
        """
        message_id = self.war_room.post(
            content=prompt,
            sender=coordinator,
            message_type="task",
            metadata={"mission": "kickoff", "step": 1},
        )
        
        # Also post to board.json for backward compatibility
        self._post_to_board(prompt, coordinator, "war-room-kickoff")
        
        return {
            "message_id": message_id,
            "channel": "war-room",
            "status": "awaiting_assessment",
        }
    
    def post_assessment(
        self,
        assessment: str,
        agent: str,
        kick_off_id: str,
        capabilities: Optional[list] = None,
    ) -> str:
        """
        Step 2: Post an assessment from an AI agent.
        
        Args:
            assessment: Agent's assessment of what they can handle
            agent: Agent name (e.g., "claude-code", "qwen-analyst")
            kick_off_id: ID of the kick-off message this is responding to
            capabilities: List of capabilities the agent is offering
            
        Returns:
            Message ID
        """
        content = f"""## Assessment by {agent}

{assessment}

**Capabilities:** {', '.join(capabilities or ['general'])}
"""
        
        return self.war_room.post(
            content=content,
            sender=agent,
            message_type="update",
            thread_id=kick_off_id,
            metadata={"mission": "assessment", "step": 2, "capabilities": capabilities or []},
        )
    
    def create_approval_plan(
        self,
        title: str,
        description: str,
        tasks: list[dict],
        coordinator: str,
        kick_off_id: Optional[str] = None,
    ) -> dict:
        """
        Step 3: Create an approval plan from assessments.
        
        Synthesizes agent assessments into a structured plan for human approval.
        
        Args:
            title: Plan title
            description: Plan description
            tasks: List of task dicts with assignee, description, etc.
            coordinator: Coordinator name
            kick_off_id: Optional reference to original kick-off
            
        Returns:
            Approval plan dict with ID
        """
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Format as markdown
        markdown_plan = self._format_approval_plan(title, description, tasks)
        
        # Post to approvals channel
        message_id = self.approvals.post(
            content=markdown_plan,
            sender=coordinator,
            message_type="plan",
            metadata={
                "plan_id": plan_id,
                "title": title,
                "tasks": tasks,
                "kick_off_id": kick_off_id,
                "status": "pending_approval",
            },
        )
        
        # Store in approvals registry
        approvals = atomic_read(APPROVALS_FILE, {"plans": {}})
        approvals["plans"][plan_id] = {
            "plan_id": plan_id,
            "title": title,
            "description": description,
            "tasks": tasks,
            "message_id": message_id,
            "status": "pending_approval",
            "created_at": datetime.now().isoformat(),
            "approved_at": None,
            "approved_by": None,
        }
        atomic_write(APPROVALS_FILE, approvals)
        
        return {
            "plan_id": plan_id,
            "message_id": message_id,
            "status": "pending_approval",
        }
    
    def _format_approval_plan(self, title: str, description: str, tasks: list[dict]) -> str:
        """Format a plan as markdown for approval."""
        lines = [
            f"# {title}",
            "",
            description,
            "",
            "## Tasks",
            "",
        ]
        
        for i, task in enumerate(tasks, 1):
            assignee = task.get("assignee", "unassigned")
            task_desc = task.get("description", "No description")
            priority = task.get("priority", "normal")
            
            lines.append(f"### Task {i}: {task.get('title', 'Untitled')}")
            lines.append(f"- **Assignee:** {assignee}")
            lines.append(f"- **Priority:** {priority}")
            lines.append(f"- **Description:** {task_desc}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("**Human approval required.** Reply with 'approved' to greenlight.")
        
        return "\n".join(lines)
    
    def approve_plan(self, plan_id: str, approved_by: str = "human") -> bool:
        """
        Step 4: Approve a plan (human gatekeeping).
        
        Args:
            plan_id: ID of the plan to approve
            approved_by: Who approved (usually "human")
            
        Returns:
            True if approved successfully
        """
        approvals = atomic_read(APPROVALS_FILE, {"plans": {}})
        
        if plan_id not in approvals.get("plans", {}):
            return False
        
        plan = approvals["plans"][plan_id]
        plan["status"] = "approved"
        plan["approved_at"] = datetime.now().isoformat()
        plan["approved_by"] = approved_by
        
        atomic_write(APPROVALS_FILE, approvals)
        
        # Post approval to approvals channel
        self.approvals.post(
            content=f"✅ **Plan Approved**\n\nPlan `{plan_id}` approved by {approved_by}.",
            sender=approved_by,
            message_type="approval",
            thread_id=plan["message_id"],
            metadata={"plan_id": plan_id, "action": "approved"},
        )
        
        return True
    
    def reject_plan(self, plan_id: str, rejected_by: str = "human", reason: str = "") -> bool:
        """
        Reject a plan.
        
        Args:
            plan_id: ID of the plan to reject
            rejected_by: Who rejected
            reason: Optional reason for rejection
            
        Returns:
            True if rejected successfully
        """
        approvals = atomic_read(APPROVALS_FILE, {"plans": {}})
        
        if plan_id not in approvals.get("plans", {}):
            return False
        
        plan = approvals["plans"][plan_id]
        plan["status"] = "rejected"
        plan["rejected_at"] = datetime.now().isoformat()
        plan["rejected_by"] = rejected_by
        plan["rejection_reason"] = reason
        
        atomic_write(APPROVALS_FILE, approvals)
        
        # Post rejection to approvals channel
        self.approvals.post(
            content=f"❌ **Plan Rejected**\n\nPlan `{plan_id}` rejected by {rejected_by}.\n\n**Reason:** {reason or 'Not specified'}",
            sender=rejected_by,
            message_type="approval",
            thread_id=plan["message_id"],
            metadata={"plan_id": plan_id, "action": "rejected", "reason": reason},
        )
        
        return True
    
    def dispatch_tasks(self, plan_id: str, dispatcher: str = "coordinator") -> list[dict]:
        """
        Step 5: Dispatch tasks from approved plan to team channels.
        
        Extracts tasks from an approved plan and posts them to appropriate team channels.
        
        Args:
            plan_id: ID of the approved plan
            dispatcher: Who is dispatching
            
        Returns:
            List of dispatched task info
        """
        approvals = atomic_read(APPROVALS_FILE, {"plans": {}})
        
        if plan_id not in approvals.get("plans", {}):
            raise ValueError(f"Plan {plan_id} not found")
        
        plan = approvals["plans"][plan_id]
        
        if plan["status"] != "approved":
            raise ValueError(f"Plan {plan_id} is not approved (status: {plan['status']})")
        
        dispatched = []
        
        for task in plan.get("tasks", []):
            assignee = task.get("assignee", "general")
            
            # Determine target channel
            if assignee.startswith("claude"):
                channel_name = "team-claude"
            elif assignee.startswith("qwen"):
                channel_name = "team-qwen"
            elif assignee.startswith("gemini"):
                channel_name = "team-gemini"
            else:
                channel_name = "tasks"  # Default channel
            
            # Get or create team channel
            team_channel = get_or_create_channel(channel_name, f"Tasks for {assignee}")
            
            # Format task message
            task_content = f"""## Task: {task.get('title', 'Untitled')}

**Assigned to:** {assignee}
**Priority:** {task.get('priority', 'normal')}
**From Plan:** {plan_id}

{task.get('description', 'No description')}
"""
            
            # Post to team channel
            message_id = team_channel.post(
                content=task_content,
                sender=dispatcher,
                message_type="task",
                metadata={
                    "plan_id": plan_id,
                    "assignee": assignee,
                    "priority": task.get("priority", "normal"),
                },
            )
            
            dispatched.append({
                "task_id": message_id,
                "channel": channel_name,
                "assignee": assignee,
            })
        
        # Update plan status
        plan["status"] = "dispatched"
        plan["dispatched_at"] = datetime.now().isoformat()
        plan["dispatched_tasks"] = dispatched
        atomic_write(APPROVALS_FILE, approvals)
        
        return dispatched
    
    def get_pending_approvals(self) -> list[dict]:
        """Get all plans pending approval."""
        approvals = atomic_read(APPROVALS_FILE, {"plans": {}})
        return [
            p for p in approvals.get("plans", {}).values()
            if p.get("status") == "pending_approval"
        ]
    
    def get_plan(self, plan_id: str) -> Optional[dict]:
        """Get a specific plan by ID."""
        approvals = atomic_read(APPROVALS_FILE, {"plans": {}})
        return approvals.get("plans", {}).get(plan_id)
    
    def _post_to_board(self, content: str, sender: str, task_type: str) -> None:
        """Post to legacy board.json for backward compatibility."""
        board_file = BOARD_DIR / "board.json"
        
        if not board_file.exists():
            board_file.write_text('{"tasks": []}')
        
        board = atomic_read(board_file, {"tasks": []})
        
        new_task = {
            "id": f"war_room_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": f"War Room: {task_type}",
            "description": content[:500],  # Truncate for board
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "claimed_by": None,
            "metadata": {
                "source": "war_room",
                "sender": sender,
                "type": task_type,
            },
        }
        
        board["tasks"].append(new_task)
        atomic_write(board_file, board)


# Global war room instance
_war_room: Optional[WarRoom] = None


def get_war_room() -> WarRoom:
    """Get the global war room instance."""
    global _war_room
    if _war_room is None:
        _war_room = WarRoom()
    return _war_room
