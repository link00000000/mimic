"""Utility functions for time."""
import asyncio
from threading import Timer
from time import time
from typing import Callable

from pyee import AsyncIOEventEmitter


def timestamp() -> int:
    """Get number of milliseconds from epoch."""
    return int(time() * 1000)


def latency(previous_timestamp: int) -> int:
    """Find the current latency in milliseconds from a previous timestamp."""
    return timestamp() - previous_timestamp


class RollingTimeout:
    """
    Function is executed after some interval.

    If `rollback` is invoked before expiration, the timer will be reset back to the original interval.
    """

    def __init__(self, interval: float, callback: Callable):
        """
        Create new instance of `RollingTimeout`.

        Args:
            interval (int): How long to wait before callback is executed (in seconds)
            callback (Callable): Funtion that is executed when the timer expires
        """
        self._interval = interval
        self._callback = callback

    async def _job(self):
        await asyncio.sleep(self._interval)
        await self._callback()

    def start(self):
        """Start the timer."""
        self._task = asyncio.ensure_future(self._job())

    def rollback(self):
        """Reset the expiration of the timer to the original interval."""
        self._task.cancel()
        self.start()

    def stop(self):
        """Stop the timer."""
        self._task.cancel()
