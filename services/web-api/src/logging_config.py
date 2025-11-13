"""Cloud Logging configuration for audit events."""
import logging
import json
from datetime import datetime
from typing import Any, Dict
from contextvars import ContextVar

# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging compatible with Cloud Logging.
    
    Formats log records as JSON with structured fields that Cloud Logging
    can parse and index for querying and analysis.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string with structured log data
        """
        # Base log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_entry["correlation_id"] = correlation_id
        
        # Add extra fields from the record
        if hasattr(record, "extra"):
            log_entry.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add source location
        log_entry["source_location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName
        }
        
        return json.dumps(log_entry)


def configure_cloud_logging():
    """
    Configure logging for Cloud Logging with structured output.
    
    Sets up:
    - Structured JSON formatting for Cloud Logging
    - Separate audit logger with INFO level
    - Correlation ID support for request tracing
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with structured formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # Configure audit logger with structured output
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False  # Don't propagate to root logger
    
    # Add handler to audit logger
    audit_handler = logging.StreamHandler()
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(StructuredFormatter())
    audit_logger.addHandler(audit_handler)
    
    logging.info("Cloud Logging configured with structured output")


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for the current request context.
    
    Args:
        correlation_id: Unique identifier for request tracing
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str:
    """
    Get correlation ID from the current request context.
    
    Returns:
        Correlation ID or empty string if not set
    """
    return correlation_id_var.get()
