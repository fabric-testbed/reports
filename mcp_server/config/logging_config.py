"""
Logging configuration for MCP Server.

Provides structured JSON logging for production and human-readable
text logging for development. Supports correlation IDs for request tracking.

Usage:
    from config.logging_config import setup_logging, get_logger, set_correlation_id

    setup_logging(settings.logging)
    logger = get_logger(__name__)
    set_correlation_id("req-abc123")
    logger.info("Server started", extra={"port": 5000})
"""

from __future__ import annotations

import contextvars
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from pythonjsonlogger import jsonlogger

from config.settings import LoggingSettings

# Correlation ID stored per-async-task / per-thread
_correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default="no-correlation-id"
)

# Standard LogRecord attributes — computed once from a throwaway record so we
# never have to maintain a hand-written exclude list.
_STANDARD_LOG_ATTRS: frozenset[str] = frozenset(
    vars(logging.LogRecord("", 0, "", 0, "", (), None)).keys()
) | {"message", "asctime", "correlation_id"}


def set_correlation_id(correlation_id: str) -> contextvars.Token[str]:
    """
    Set correlation ID for the current context (async task / thread).

    The ID is automatically added to all log records produced in the
    same context via ``CorrelationIdFilter``.

    Args:
        correlation_id: Unique correlation ID for request tracking

    Returns:
        A token that can be used to reset the value.
    """
    return _correlation_id_var.set(correlation_id)


class CorrelationIdFilter(logging.Filter):
    """
    Add correlation ID to log records.

    Reads from the ``_correlation_id_var`` contextvar so every log
    message automatically inherits the ID set for the current context.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation_id to log record from contextvar."""
        record.correlation_id = _correlation_id_var.get()  # type: ignore[attr-defined]
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured logging.

    Formats log records as JSON with standard fields:
    - timestamp: ISO8601 timestamp
    - level: Log level (DEBUG, INFO, etc.)
    - logger: Logger name
    - message: Log message
    - correlation_id: Request correlation ID
    - Additional fields from extra dict
    """

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict):
        """Add custom fields to JSON log record."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["message"] = record.getMessage()

        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id

        # Add exception info if present
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        # Add extra fields (passed via extra={} parameter)
        for key, value in message_dict.items():
            if key not in log_record:
                log_record[key] = value


class CustomTextFormatter(logging.Formatter):
    """
    Custom text formatter for human-readable logging.

    Format: YYYY-MM-DD HH:MM:SS LEVEL [correlation_id] logger - message
    """

    def __init__(self):
        """Initialize text formatter with standard format."""
        fmt = "%(asctime)s %(levelname)-8s [%(correlation_id)s] %(name)s - %(message)s"
        super().__init__(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text, appending any extra fields."""
        # Ensure correlation_id is set (belt-and-suspenders; filter should handle it)
        if not hasattr(record, "correlation_id"):
            record.correlation_id = _correlation_id_var.get()  # type: ignore[attr-defined]

        msg = super().format(record)

        # Append non-standard extra fields
        extra_fields = [
            f"{key}={value}"
            for key, value in record.__dict__.items()
            if key not in _STANDARD_LOG_ATTRS
        ]

        if extra_fields:
            msg += f" ({', '.join(extra_fields)})"

        return msg


def parse_rotation_size(size_str: str) -> int:
    """
    Parse rotation size string to bytes.

    Args:
        size_str: Size string (e.g., '100MB', '1GB')

    Returns:
        Size in bytes
    """
    size_str = size_str.upper().strip()

    multipliers = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
    }

    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            try:
                value = float(size_str[: -len(suffix)])
                return int(value * multiplier)
            except ValueError:
                pass

    try:
        return int(size_str)
    except ValueError:
        raise ValueError(f"Invalid rotation size: {size_str}")


def setup_logging(settings: LoggingSettings) -> logging.Logger:
    """
    Set up logging based on settings.

    Args:
        settings: Logging configuration settings

    Returns:
        Root logger instance
    """
    logger = logging.getLogger("mcp_server")
    logger.setLevel(getattr(logging, settings.level))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Choose formatter based on format setting
    if settings.format == "json":
        formatter = CustomJsonFormatter()
    else:
        formatter = CustomTextFormatter()

    # Add correlation ID filter
    correlation_filter = CorrelationIdFilter()
    logger.addFilter(correlation_filter)

    # Add stdout handler if needed
    if settings.destination in ["stdout", "both"]:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

    # Add file handler if needed
    if settings.destination in ["file", "both"]:
        if not settings.file_path:
            raise ValueError("file_path is required when destination includes 'file'")

        log_path = Path(settings.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        max_bytes = parse_rotation_size(settings.rotation_size)

        file_handler = logging.handlers.RotatingFileHandler(
            settings.file_path,
            maxBytes=max_bytes,
            backupCount=settings.retention_days,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    All loggers are children of 'mcp_server' root logger,
    so they inherit the configuration from setup_logging().

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    if not name.startswith("mcp_server"):
        name = f"mcp_server.{name}"

    return logging.getLogger(name)
