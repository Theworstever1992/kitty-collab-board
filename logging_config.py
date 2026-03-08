"""
logging_config.py — Kitty Collab Board
Structured logging configuration using Python's standard logging module.

Replaces custom logging with JSON-formatted, rotating log files.
"""

import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add agent name if available
        if hasattr(record, "agent_name"):
            log_data["agent"] = record.agent_name
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName",
                          "levelname", "levelno", "lineno", "module", "msecs",
                          "pathname", "process", "processName", "relativeCreated",
                          "stack_info", "exc_info", "exc_text", "thread", "threadName",
                          "agent_name"]:
                log_data[key] = value
        
        return json.dumps(log_data)


class AgentLogAdapter(logging.LoggerAdapter):
    """Logger adapter that adds agent name to all log records."""
    
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        extra["agent_name"] = self.extra.get("agent_name", "unknown")
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging(
    log_dir: Path,
    agent_name: Optional[str] = None,
    level: int = logging.INFO,
    console_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Set up structured logging for an agent or service.
    
    Args:
        log_dir: Directory for log files
        agent_name: Name of agent (for log file naming and context)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        console_output: Whether to also log to console
        max_bytes: Max size per log file before rotation
        backup_count: Number of backup log files to keep
    
    Returns:
        Configured logger instance
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger_name = f"clowder.{agent_name}" if agent_name else "clowder"
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # JSON formatter
    json_formatter = JSONFormatter()
    
    # Human-readable formatter for console
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(agent_name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler (JSON, rotating)
    if agent_name:
        log_file = log_dir / f"{agent_name}.log"
    else:
        log_file = log_dir / "clowder.log"
    
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (human-readable)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        
        # Add agent_name to console records
        if agent_name:
            old_factory = logging.getLogRecordFactory()
            
            def record_factory(*args, **kwargs):
                record = old_factory(*args, **kwargs)
                record.agent_name = agent_name
                return record
            
            logging.setLogRecordFactory(record_factory)
        
        logger.addHandler(console_handler)
    
    # Wrap with AgentLogAdapter if agent_name provided
    if agent_name:
        return AgentLogAdapter(logger, {"agent_name": agent_name})
    
    return logger


def get_logger(name: str, agent_name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger with the given name.
    
    Args:
        name: Logger name (usually __name__)
        agent_name: Optional agent name for context
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    if agent_name and not isinstance(logger, AgentLogAdapter):
        return AgentLogAdapter(logger, {"agent_name": agent_name})
    
    return logger


# Convenience functions for common log levels
def debug(msg: str, logger: Optional[logging.Logger] = None, **kwargs):
    """Log debug message."""
    if logger:
        logger.debug(msg, extra=kwargs)

def info(msg: str, logger: Optional[logging.Logger] = None, **kwargs):
    """Log info message."""
    if logger:
        logger.info(msg, extra=kwargs)

def warning(msg: str, logger: Optional[logging.Logger] = None, **kwargs):
    """Log warning message."""
    if logger:
        logger.warning(msg, extra=kwargs)

def error(msg: str, logger: Optional[logging.Logger] = None, **kwargs):
    """Log error message."""
    if logger:
        logger.error(msg, extra=kwargs)

def critical(msg: str, logger: Optional[logging.Logger] = None, **kwargs):
    """Log critical message."""
    if logger:
        logger.critical(msg, extra=kwargs)


if __name__ == "__main__":
    # Test logging setup
    from config import get_config
    
    config = get_config()
    logger = setup_logging(
        log_dir=config.board.log_dir,
        agent_name="test_agent",
        level=logging.DEBUG
    )
    
    print("Testing structured logging...\n")
    
    info("This is an info message", logger=logger)
    warning("This is a warning", logger=logger)
    error("This is an error", logger=logger)
    
    try:
        raise ValueError("Test exception")
    except Exception:
        error("Exception occurred", logger=logger, exc_info=True)
    
    print(f"\n✅ Logs written to: {config.board.log_dir / 'test_agent.log'}")
    print("Check the file for JSON-formatted logs!")
