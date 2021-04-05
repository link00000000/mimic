"""Standard formatter for logging."""
import logging

log_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
)
