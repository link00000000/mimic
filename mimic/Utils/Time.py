"""Utility functions for time."""

from time import time


def timestamp() -> int:
    """Get number of milliseconds from epoch."""
    return int(time() * 1000)


def latency(previous_timestamp: int) -> int:
    """Find the current latency in milliseconds from a previous timestamp."""
    return timestamp() - previous_timestamp
