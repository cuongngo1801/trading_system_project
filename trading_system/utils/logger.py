"""Structured logging configuration for trading system."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog


def configure_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None,
    service_name: str = "trading-system",
) -> None:
    """Configure structured logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type (json, console)
        log_file: Optional log file path
        service_name: Service name for logging context
    """
    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure timestamper
    timestamper = structlog.processors.TimeStamper(fmt="ISO")

    # Configure processors based on format type
    if format_type.lower() == "json":
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            timestamper,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            timestamper,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Add file handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        handlers.append(file_handler)

    logging.basicConfig(format="%(message)s", level=log_level, handlers=handlers)


class TradingLogger:
    """Trading system logger with context management."""

    def __init__(self, name: str, context: Optional[Dict[str, Any]] = None):
        """Initialize logger with context.

        Args:
            name: Logger name
            context: Additional context for logging
        """
        self.logger = structlog.get_logger(name)
        self.context = context or {}

        # Add default context
        self.context.update(
            {
                "service": "trading-system",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "version": "1.0.0",
            }
        )

    def with_context(self, **kwargs) -> "TradingLogger":
        """Add context to logger.

        Args:
            **kwargs: Context key-value pairs

        Returns:
            New logger instance with added context
        """
        new_context = {**self.context, **kwargs}
        return TradingLogger(self.logger._context.get("logger", "trading"), new_context)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **{**self.context, **kwargs})

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **{**self.context, **kwargs})

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **{**self.context, **kwargs})

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, **{**self.context, **kwargs})

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, **{**self.context, **kwargs})

    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, **{**self.context, **kwargs})


class PerformanceLogger:
    """Performance logging for trading operations."""

    def __init__(self, logger: TradingLogger):
        """Initialize performance logger.

        Args:
            logger: Base logger instance
        """
        self.logger = logger.with_context(component="performance")

    def log_execution_time(self, operation: str, duration: float, **kwargs) -> None:
        """Log operation execution time.

        Args:
            operation: Operation name
            duration: Duration in seconds
            **kwargs: Additional context
        """
        self.logger.info(
            f"Operation completed: {operation}",
            operation=operation,
            duration_seconds=duration,
            duration_ms=duration * 1000,
            **kwargs,
        )

    def log_trade_execution(
        self,
        symbol: str,
        action: str,
        quantity: float,
        price: float,
        execution_time: float,
        **kwargs,
    ) -> None:
        """Log trade execution details.

        Args:
            symbol: Trading symbol
            action: Trade action (buy/sell)
            quantity: Trade quantity
            price: Execution price
            execution_time: Execution time in seconds
            **kwargs: Additional context
        """
        self.logger.info(
            f"Trade executed: {action} {quantity} {symbol} @ {price}",
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            execution_time_ms=execution_time * 1000,
            **kwargs,
        )

    def log_signal_generation(
        self,
        symbol: str,
        signal_type: str,
        strength: float,
        generation_time: float,
        **kwargs,
    ) -> None:
        """Log signal generation.

        Args:
            symbol: Trading symbol
            signal_type: Signal type (buy/sell/hold)
            strength: Signal strength (0-1)
            generation_time: Generation time in seconds
            **kwargs: Additional context
        """
        self.logger.info(
            f"Signal generated: {signal_type} for {symbol}",
            symbol=symbol,
            signal_type=signal_type,
            signal_strength=strength,
            generation_time_ms=generation_time * 1000,
            **kwargs,
        )


class AuditLogger:
    """Audit logging for compliance and security."""

    def __init__(self, logger: TradingLogger):
        """Initialize audit logger.

        Args:
            logger: Base logger instance
        """
        self.logger = logger.with_context(component="audit")

    def log_user_action(
        self, user_id: str, action: str, resource: str, **kwargs
    ) -> None:
        """Log user action for audit trail.

        Args:
            user_id: User identifier
            action: Action performed
            resource: Resource accessed
            **kwargs: Additional context
        """
        self.logger.info(
            f"User action: {user_id} performed {action} on {resource}",
            user_id=user_id,
            action=action,
            resource=resource,
            timestamp=datetime.utcnow().isoformat(),
            **kwargs,
        )

    def log_config_change(
        self, config_key: str, old_value: Any, new_value: Any, user_id: str
    ) -> None:
        """Log configuration changes.

        Args:
            config_key: Configuration key changed
            old_value: Previous value
            new_value: New value
            user_id: User who made the change
        """
        self.logger.warning(
            f"Configuration changed: {config_key}",
            config_key=config_key,
            old_value=str(old_value),
            new_value=str(new_value),
            changed_by=user_id,
            timestamp=datetime.utcnow().isoformat(),
        )

    def log_security_event(
        self, event_type: str, severity: str, details: Dict[str, Any]
    ) -> None:
        """Log security events.

        Args:
            event_type: Type of security event
            severity: Event severity (low/medium/high/critical)
            details: Event details
        """
        self.logger.error(
            f"Security event: {event_type}",
            event_type=event_type,
            severity=severity,
            details=details,
            timestamp=datetime.utcnow().isoformat(),
        )


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> TradingLogger:
    """Get a logger instance with optional context.

    Args:
        name: Logger name
        context: Optional context dictionary

    Returns:
        TradingLogger instance
    """
    return TradingLogger(name, context)


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get a performance logger instance.

    Args:
        name: Logger name

    Returns:
        PerformanceLogger instance
    """
    base_logger = get_logger(name)
    return PerformanceLogger(base_logger)


def get_audit_logger(name: str) -> AuditLogger:
    """Get an audit logger instance.

    Args:
        name: Logger name

    Returns:
        AuditLogger instance
    """
    base_logger = get_logger(name)
    return AuditLogger(base_logger)
