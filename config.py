"""
config.py — Kitty Collab Board
Centralized configuration system with environment validation.

Supports multiple environments (dev, staging, prod) and loads from .env files.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


@dataclass
class BoardConfig:
    """Board-related configuration."""
    board_dir: Path = field(default_factory=lambda: Path(__file__).parent / "board")
    log_dir: Path = field(default_factory=lambda: Path(__file__).parent / "logs")
    archive_after_days: int = 30
    stale_task_minutes: int = 5
    handoff_timeout_minutes: int = 10


@dataclass
class AgentConfig:
    """Agent-related configuration."""
    default_poll_interval: float = 5.0  # seconds
    task_timeout_minutes: int = 5
    max_retries: int = 3
    retry_base_delay: float = 1.0  # seconds
    retry_max_delay: float = 60.0  # seconds
    heartbeat_interval: float = 30.0  # seconds


@dataclass
class APIConfig:
    """API key configuration."""
    anthropic_api_key: Optional[str] = None
    dashscope_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"


@dataclass
class WebConfig:
    """Web server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ])
    reload: bool = True  # Auto-reload in development


@dataclass
class AlertConfig:
    """Alert/notification configuration."""
    discord_webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    agent_offline_threshold: int = 300  # seconds (5 minutes)
    agent_warning_threshold: int = 60  # seconds (1 minute)
    rate_limit_warning_count: int = 3  # warnings before alert


@dataclass
class Config:
    """Main configuration container."""
    environment: str = "dev"
    debug: bool = True
    board: BoardConfig = field(default_factory=BoardConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    api: APIConfig = field(default_factory=APIConfig)
    web: WebConfig = field(default_factory=WebConfig)
    alert: AlertConfig = field(default_factory=AlertConfig)
    
    def validate(self) -> list[str]:
        """
        Validate configuration and return list of errors.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Check for at least one API key
        if not any([
            self.api.anthropic_api_key,
            self.api.dashscope_api_key,
            self.api.gemini_api_key,
            self.api.openai_api_key,
        ]):
            errors.append(
                "At least one API key must be set "
                "(ANTHROPIC_API_KEY, DASHSCOPE_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY)"
            )
        
        # Validate directories
        if not self.board.board_dir.exists():
            try:
                self.board.board_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create board directory: {e}")
        
        if not self.board.log_dir.exists():
            try:
                self.board.log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create log directory: {e}")
        
        # Validate web port
        if not (1 <= self.web.port <= 65535):
            errors.append(f"Invalid web port: {self.web.port}")
        
        # Validate thresholds
        if self.alert.agent_warning_threshold >= self.alert.agent_offline_threshold:
            errors.append(
                "agent_warning_threshold must be less than agent_offline_threshold"
            )
        
        return errors


def load_config(env_file: Optional[str] = None, environment: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables and .env file.
    
    Args:
        env_file: Path to .env file (default: project root .env)
        environment: Environment name (dev, staging, prod)
    
    Returns:
        Config object with all settings
    """
    # Load .env file
    if DOTENV_AVAILABLE:
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env in project root
            project_root = Path(__file__).parent
            for parent in [project_root] + list(project_root.parents):
                env_path = parent / ".env"
                if env_path.exists():
                    load_dotenv(env_path)
                    break
    
    # Get environment
    env = environment or os.environ.get("CLOWDER_ENV", "dev")
    debug = os.environ.get("CLOWDER_DEBUG", "true").lower() == "true"
    
    # Board config
    board_dir = Path(os.environ.get(
        "CLOWDER_BOARD_DIR",
        Path(__file__).parent / "board"
    ))
    log_dir = Path(os.environ.get(
        "CLOWDER_LOG_DIR",
        Path(__file__).parent / "logs"
    ))
    archive_days = int(os.environ.get("CLOWDER_ARCHIVE_AFTER_DAYS", "30"))
    stale_minutes = int(os.environ.get("CLOWDER_STALE_TASK_MINUTES", "5"))
    handoff_timeout = int(os.environ.get("CLOWDER_HANDOFF_TIMEOUT_MINUTES", "10"))
    
    # Agent config
    poll_interval = float(os.environ.get("CLOWDER_POLL_INTERVAL", "5.0"))
    task_timeout = int(os.environ.get("CLOWDER_TASK_TIMEOUT_MINUTES", "5"))
    max_retries = int(os.environ.get("CLOWDER_MAX_RETRIES", "3"))
    retry_base = float(os.environ.get("CLOWDER_RETRY_BASE_DELAY", "1.0"))
    retry_max = float(os.environ.get("CLOWDER_RETRY_MAX_DELAY", "60.0"))
    heartbeat = float(os.environ.get("CLOWDER_HEARTBEAT_INTERVAL", "30.0"))
    
    # API config
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    dashscope_key = os.environ.get("DASHSCOPE_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Web config
    web_host = os.environ.get("CLOWDER_WEB_HOST", "0.0.0.0")
    web_port = int(os.environ.get("CLOWDER_WEB_PORT", "8000"))
    cors = os.environ.get(
        "CLOWDER_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    web_reload = os.environ.get("CLOWDER_WEB_RELOAD", "true").lower() == "true"
    
    # Alert config
    discord_url = os.environ.get("CLOWDER_DISCORD_WEBHOOK_URL")
    slack_url = os.environ.get("CLOWDER_SLACK_WEBHOOK_URL")
    offline_threshold = int(os.environ.get("CLOWDER_AGENT_OFFLINE_SECONDS", "300"))
    warning_threshold = int(os.environ.get("CLOWDER_AGENT_WARNING_SECONDS", "60"))
    rate_limit_count = int(os.environ.get("CLOWDER_RATE_LIMIT_WARNINGS", "3"))
    
    return Config(
        environment=env,
        debug=debug,
        board=BoardConfig(
            board_dir=board_dir,
            log_dir=log_dir,
            archive_after_days=archive_days,
            stale_task_minutes=stale_minutes,
            handoff_timeout_minutes=handoff_timeout,
        ),
        agent=AgentConfig(
            default_poll_interval=poll_interval,
            task_timeout_minutes=task_timeout,
            max_retries=max_retries,
            retry_base_delay=retry_base,
            retry_max_delay=retry_max,
            heartbeat_interval=heartbeat,
        ),
        api=APIConfig(
            anthropic_api_key=anthropic_key,
            dashscope_api_key=dashscope_key,
            gemini_api_key=gemini_key,
            openai_api_key=openai_key,
            ollama_base_url=ollama_url,
        ),
        web=WebConfig(
            host=web_host,
            port=web_port,
            cors_origins=cors,
            reload=web_reload,
        ),
        alert=AlertConfig(
            discord_webhook_url=discord_url,
            slack_webhook_url=slack_url,
            agent_offline_threshold=offline_threshold,
            agent_warning_threshold=warning_threshold,
            rate_limit_warning_count=rate_limit_count,
        ),
    )


# Global config instance (lazy-loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance, loading if necessary."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> Config:
    """Force reload of global config."""
    global _config
    _config = load_config()
    return _config


# Convenience function for validation
def validate_config() -> tuple[Config, list[str]]:
    """
    Load and validate configuration.
    
    Returns:
        Tuple of (config, errors)
        If errors is empty, config is valid
    """
    config = load_config()
    errors = config.validate()
    return config, errors


if __name__ == "__main__":
    # Test configuration loading
    print("Loading configuration...")
    config, errors = validate_config()
    
    print(f"\nEnvironment: {config.environment}")
    print(f"Debug: {config.debug}")
    print(f"\nBoard directory: {config.board.board_dir}")
    print(f"Log directory: {config.board.log_dir}")
    
    if errors:
        print("\n⚠️ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ Configuration valid!")
