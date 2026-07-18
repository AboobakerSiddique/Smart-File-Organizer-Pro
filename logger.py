"""
Logging setup for Smart File Organizer Pro.

Provides a single, application-wide logger that writes plain text to a
rotating log file (logs/organizer.log) and colorized output to the
console when the terminal supports ANSI escape codes.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

import config


class _ColorFormatter(logging.Formatter):
    """Formatter that adds ANSI colors to console output when supported."""

    LEVEL_COLORS = {
        "DEBUG": "\033[36m",     # cyan
        "INFO": "\033[37m",      # white
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[41m",  # red background
    }
    MOVED_COLOR = "\033[32m"     # green, highlights successful moves
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color = self.LEVEL_COLORS.get(record.levelname, "")
        if "[MOVED]" in message:
            color = self.MOVED_COLOR
        if not color:
            return message
        return f"{color}{message}{self.RESET}"


def _supports_color() -> bool:
    """Best-effort detection of ANSI color support on the current stream."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def get_logger(name: str = "SmartFileOrganizer") -> logging.Logger:
    """
    Create (or retrieve) the application-wide logger.

    Configures a rotating file handler and a console handler exactly
    once per process, so calling this repeatedly from different modules
    is always safe and never duplicates log lines.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))

    config.LOG_DIR.mkdir(parents=True, exist_ok=True)

    plain_formatter = logging.Formatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)

    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(plain_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    if _supports_color():
        console_handler.setFormatter(
            _ColorFormatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)
        )
    else:
        console_handler.setFormatter(plain_formatter)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger
