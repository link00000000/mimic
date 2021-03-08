"""
Asynchronous file logging for Python's built-in logging library.

Logs are written to disk without blocking the main thread.

>>> import logging
>>> my_logger = logging.getLogger()
>>> asyncHandler = AsyncLoggingHandler("myLogFile.log")
>>> my_logger.addHandler(asyncHandler)
>>> my_logger.info("This will be logged to myLogFile.log without blocking the main thread")
"""
from abc import ABC
from logging import FileHandler, LogRecord
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from queue import Queue
from threading import Thread


class _AsyncHandler(ABC, object):
    """
    Abstract classes to log files to the disk without blocking the main thread.

    Provides non-blocking file writing of logs. Uses a `Queue` to write to the
    file using a spearate thread.

    @NOTE Should be inheritted from and not used directly

    Adapted from https://github.com/CopterExpress/python-async-logging-handler
    """

    def __init__(self, *args, **kwargs):
        """
        Spawn file logging handler.

        Spawn a file logging handler on a separate thread and estabslish communication
        with the main thread.
        """
        super(_AsyncHandler, self).__init__(*args, *kwargs)
        self.__queue = Queue(-1)
        self.__thread = Thread(target=self.__loop)
        self.__thread.daemon = True
        self.__thread.start()

    def emit(self, record: LogRecord):
        """
        Place new `LogRecord` in logging queue.

        @NOTE Called by Python's built-in logging library. Should *not* be called directly

        Args:
            record (logging.LogRecord): New log message
        """
        self.__queue.put(record)

    def __loop(self):
        """
        Remove `LogRecord`s from the the queue and write them to file.

        @NOTE Should *not* be called directly, this process does not run on the
        main thread.
        """
        while True:
            record = self.__queue.get()
            try:
                super(_AsyncHandler, self).emit(record)
            except:
                pass


class AsyncFileHandler(_AsyncHandler, FileHandler):
    """Non-blocking alternative to `FileHandler`."""

    pass


class AsyncRotatingFileHanlder(_AsyncHandler, RotatingFileHandler):
    """Non-blocking alternative to `RotatingFileHandler`."""

    pass


class AsyncTimedRotatingFileHandler(_AsyncHandler, TimedRotatingFileHandler):
    """Non-blocking alternative to `TimedRotatingFileHandler`."""

    pass
