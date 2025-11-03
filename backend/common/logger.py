import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for different log levels."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m\033[37m",  # White on Red background
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and context."""
        # Add colors to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{self.BOLD}{levelname:8}{self.RESET}"
            )

        # Color the logger name (service/class)
        record.name = f"{self.DIM}{record.name}{self.RESET}"

        # Format timestamp
        record.asctime = self.formatTime(record, self.datefmt)
        record.asctime = f"{self.DIM}{record.asctime}{self.RESET}"

        # Format the message
        formatted = super().format(record)

        # Reset levelname for further processing
        record.levelname = levelname

        return formatted


class FileFormatter(logging.Formatter):
    """Plain formatter for file output without colors."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record without colors for file output."""
        return super().format(record)


def setup_logger(
    name: str,
    level: Optional[int] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Create and configure a logger with console and optional file output.

    Args:
        name: Logger name (usually __name__ from the calling module)
        level: Logging level (defaults to DEBUG in dev, INFO in production)
        log_file: Optional file path for logging to file

    Returns:
        Configured logger instance

    Example:
        ```python
        from common.logger import setup_logger

        logger = setup_logger(__name__)
        logger.info("Application started")
        logger.debug("Debug information")
        logger.warning("Warning message")
        logger.error("Error occurred")
        ```
    """
    logger = logging.getLogger(name)

    # Set log level based on environment
    if level is None:
        level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Console format with colors
    console_format = (
        "%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    console_formatter = ColoredFormatter(
        console_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)

        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            log_path / log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level)

        # File format without colors
        file_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
        file_formatter = FileFormatter(
            file_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger for the given name.
    This is a convenience function for quick logger creation.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance

    Example:
        ```python
        from common.logger import get_logger

        logger = get_logger(__name__)
        logger.info("User logged in", extra={"user_id": 123})
        ```
    """
    return setup_logger(name)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.

    Usage:
        ```python
        from common.logger import LoggerMixin

        class UserService(LoggerMixin):
            def create_user(self, email: str):
                self.logger.info(f"Creating user: {email}")
                # ... rest of the code
        ```
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger


# Application-wide logger instance
app_logger = setup_logger("app", log_file="app.log")


def log_request(method: str, path: str, status_code: int, duration_ms: float) -> None:
    """
    Log HTTP request information.

    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    logger = get_logger("http")
    level = logging.INFO if status_code < 400 else logging.ERROR

    logger.log(
        level,
        f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
    )


def log_exception(exc: Exception, context: Optional[str] = None) -> None:
    """
    Log exception with full traceback.

    Args:
        exc: Exception to log
        context: Optional context information
    """
    logger = get_logger("exception")
    msg = f"Exception: {context}" if context else "Exception occurred"
    logger.exception(msg, exc_info=exc)


def log_database_query(
    query: str, duration_ms: float, rows: Optional[int] = None
) -> None:
    """
    Log database query execution.

    Args:
        query: SQL query
        duration_ms: Query execution time in milliseconds
        rows: Number of rows affected/returned
    """
    logger = get_logger("database")
    rows_info = f" ({rows} rows)" if rows is not None else ""
    logger.debug(f"Query executed in {duration_ms:.2f}ms{rows_info}: {query[:100]}...")


# Configure root logger
def configure_root_logger() -> None:
    """Configure the root logger for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    # Only show warnings and above for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)


# Initialize on import
configure_root_logger()
