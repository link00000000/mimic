from abc import ABC
from logging import FileHandler, LogRecord
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from queue import Queue
from threading import Thread


class _AsyncHandler(ABC, object):
    """
    Provides non-blocking file writing of logs. Uses a `Queue` to write to the
    file using a spearate thread.

    Adapted from https://github.com/CopterExpress/python-async-logging-handler
    """

    def __init__(self, *args, **kwargs):
        super(_AsyncHandler, self).__init__(*args, *kwargs)
        self.__queue = Queue(-1)
        self.__thread = Thread(target=self.__loop)
        self.__thread.daemon = True
        self.__thread.start()

    def emit(self, record: LogRecord):
        """
        Place new `LogRecord` in logging queue

        @NOTE Should *not* be called directly

        Args:
            record (logging.LogRecord): New log message
        """
        self.__queue.put(record)

    def __loop(self):
        """
        Remove `LogRecord`s from the the queue and write them to file

        @NOTE Should *not* be called directly, this process does not run on the
        main thread
        """
        while True:
            record = self.__queue.get()
            try:
                super(_AsyncHandler, self).emit(record)
            except:
                pass


class AsyncFileHandler(_AsyncHandler, FileHandler):
    """
    Non-blocking alternative to `FileHandler`
    """
    pass


class AsyncRotatingFileHanlder(_AsyncHandler, RotatingFileHandler):
    """
    Non-blocking alternative to `RotatingFileHandler`
    """
    pass


class AsyncTimedRotatingFileHandler(_AsyncHandler, TimedRotatingFileHandler):
    """
    Non-blocking alternative to `TimedRotatingFileHandler`
    """
    pass
