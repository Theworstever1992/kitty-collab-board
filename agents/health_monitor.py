"""
health_monitor.py — Kitty Collab Board
Tracks agent heartbeats and fires alerts when agents go offline.

Thresholds:
  - No heartbeat 60s  → warning
  - No heartbeat 300s → offline (critical)
  - Multiple API errors → rate limit warning

Alert channels: console, log file, webhook (Discord/Slack)
"""

import json
import os
import time
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

BOARD_DIR = Path(
    os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent.parent / "board")
)
LOG_DIR = Path(os.environ.get("CLOWDER_LOG_DIR", Path(__file__).parent.parent / "logs"))

# Support both legacy names and the canonical CLOWDER_ names from config.py
WARNING_THRESHOLD = int(
    os.environ.get("CLOWDER_AGENT_WARNING_SECONDS")
    or os.environ.get("HEALTH_WARNING_SECONDS", "60")
)
OFFLINE_THRESHOLD = int(
    os.environ.get("CLOWDER_AGENT_OFFLINE_SECONDS")
    or os.environ.get("HEALTH_OFFLINE_SECONDS", "300")
)


# ------------------------------------------------------------------
# Data classes
# ------------------------------------------------------------------

@dataclass
class AgentHealth:
    name: str
    status: str          # "online" | "warning" | "offline" | "unknown"
    last_seen: Optional[str]
    seconds_since: Optional[float]
    model: Optional[str] = None
    role: Optional[str] = None


@dataclass
class Alert:
    agent: str
    level: str           # "warning" | "critical"
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


# ------------------------------------------------------------------
# Webhook sender (Discord / Slack / generic)
# ------------------------------------------------------------------

class WebhookSender:
    """
    Send alerts to a webhook endpoint.

    Discord and Slack both accept a JSON body with a "content" or "text" field.
    The format is auto-detected from the URL.
    """

    def __init__(self, url: str, timeout: int = 10):
        self.url = url
        self.timeout = timeout

    def _build_payload(self, alert: Alert) -> dict:
        emoji = "⚠️" if alert.level == "warning" else "🔴"
        text = f"{emoji} **Clowder Health Alert** — agent `{alert.agent}` is {alert.level.upper()}\n{alert.reason} ({alert.timestamp})"

        if "discord" in self.url:
            return {"content": text}
        # Slack (and generic)
        return {"text": text}

    def send(self, alert: Alert) -> bool:
        if not REQUESTS_AVAILABLE:
            return False
        try:
            payload = self._build_payload(alert)
            resp = requests.post(self.url, json=payload, timeout=self.timeout)
            return resp.status_code < 300
        except Exception:
            return False


# ------------------------------------------------------------------
# Alert channel registry
# ------------------------------------------------------------------

class AlertChannels:
    """
    Configurable alert delivery.

    Channels:
      - "console"  — print to stdout
      - "log"      — write to logs/health_monitor.log
      - "webhook"  — POST to one or more webhook URLs
    """

    def __init__(self, channels: list[str] = None, webhook_urls: list[str] = None):
        self.channels = set(channels or ["console", "log"])
        self.webhook_urls = webhook_urls or []
        self._senders = [WebhookSender(u) for u in self.webhook_urls]

        if "log" in self.channels:
            LOG_DIR.mkdir(exist_ok=True)
            log_file = LOG_DIR / "health_monitor.log"
            logging.basicConfig(
                filename=str(log_file),
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(message)s",
            )
            self._logger = logging.getLogger("health_monitor")
        else:
            self._logger = None

    def fire(self, alert: Alert):
        msg = f"[{alert.level.upper()}] agent={alert.agent} — {alert.reason}"

        if "console" in self.channels:
            print(f"[HEALTH] {msg}")

        if "log" in self.channels and self._logger:
            if alert.level == "warning":
                self._logger.warning(msg)
            else:
                self._logger.error(msg)

        if "webhook" in self.channels:
            for sender in self._senders:
                sender.send(alert)


# ------------------------------------------------------------------
# HealthMonitor
# ------------------------------------------------------------------

class HealthMonitor:
    """
    Monitors agent heartbeats and emits alerts when thresholds are crossed.

    Usage (one-shot check):
        monitor = HealthMonitor()
        healths = monitor.check_agents()
        alerts  = monitor.get_alerts()

    Usage (background thread):
        monitor = HealthMonitor(channels=AlertChannels(["console", "webhook"],
                                                       ["https://discord.com/..."])
        monitor.start(interval=30)
        # ...
        monitor.stop()
    """

    def __init__(
        self,
        board_dir: Path = None,
        channels: AlertChannels = None,
        warning_threshold: int = WARNING_THRESHOLD,
        offline_threshold: int = OFFLINE_THRESHOLD,
    ):
        self.board_dir = board_dir or BOARD_DIR
        self.channels = channels or AlertChannels()
        self.warning_threshold = warning_threshold
        self.offline_threshold = offline_threshold

        self._active_alerts: dict[str, Alert] = {}   # agent → current alert
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Core check
    # ------------------------------------------------------------------

    def _load_agents(self) -> dict:
        agents_file = self.board_dir / "agents.json"
        if not agents_file.exists():
            return {}
        try:
            return json.loads(agents_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _seconds_since(self, iso_timestamp: str) -> Optional[float]:
        try:
            last = datetime.fromisoformat(iso_timestamp)
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            now = datetime.now(tz=timezone.utc)
            return (now - last).total_seconds()
        except Exception:
            return None

    def _compute_status(self, seconds: Optional[float]) -> str:
        if seconds is None:
            return "unknown"
        if seconds < self.warning_threshold:
            return "online"
        if seconds < self.offline_threshold:
            return "warning"
        return "offline"

    def check_agents(self) -> list[AgentHealth]:
        """Check all agents and return their health status."""
        agents = self._load_agents()
        results = []

        for name, info in agents.items():
            last_seen = info.get("last_seen")
            seconds = self._seconds_since(last_seen) if last_seen else None
            status = self._compute_status(seconds)

            health = AgentHealth(
                name=name,
                status=status,
                last_seen=last_seen,
                seconds_since=round(seconds, 1) if seconds is not None else None,
                model=info.get("model"),
                role=info.get("role"),
            )
            results.append(health)
            self._process_health(health)

        return results

    def _process_health(self, health: AgentHealth):
        """Fire or clear alerts based on agent health."""
        name = health.name
        prev = self._active_alerts.get(name)

        if health.status == "online":
            # Recovered — clear any existing alert
            if prev:
                del self._active_alerts[name]
            return

        if health.status == "warning":
            level = "warning"
            reason = f"No heartbeat for {health.seconds_since}s (threshold: {self.warning_threshold}s)"
        elif health.status == "offline":
            level = "critical"
            reason = f"Agent offline — no heartbeat for {health.seconds_since}s (threshold: {self.offline_threshold}s)"
        else:
            return  # unknown — skip

        # Only fire if status changed or no existing alert
        if prev is None or prev.level != level:
            alert = Alert(agent=name, level=level, reason=reason)
            self._active_alerts[name] = alert
            self.channels.fire(alert)

    def get_alerts(self) -> list[Alert]:
        """Return currently active alerts."""
        return list(self._active_alerts.values())

    def get_summary(self) -> dict:
        """Return a summary dict suitable for API responses."""
        healths = self.check_agents()
        alerts = self.get_alerts()
        return {
            "checked_at": datetime.now().isoformat(),
            "agents": [asdict(h) for h in healths],
            "alerts": [a.to_dict() for a in alerts],
            "counts": {
                "online": sum(1 for h in healths if h.status == "online"),
                "warning": sum(1 for h in healths if h.status == "warning"),
                "offline": sum(1 for h in healths if h.status == "offline"),
                "total": len(healths),
            },
        }

    # ------------------------------------------------------------------
    # Background thread
    # ------------------------------------------------------------------

    def start(self, interval: int = 30):
        """Start monitoring in a background thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(interval,),
            daemon=True,
            name="HealthMonitor",
        )
        self._thread.start()

    def stop(self):
        """Stop the background monitoring thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self, interval: int):
        while not self._stop_event.is_set():
            try:
                self.check_agents()
            except Exception:
                pass
            self._stop_event.wait(interval)
