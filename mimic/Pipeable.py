"""Helpers to establish duplex communication between processes."""

import logging
from abc import ABC
from multiprocessing import Pipe
from multiprocessing.connection import Connection
from typing import Any


class Pipeable(ABC):
    """
    Allows for inter-process communication (IPC) from a class.

    @NOTE This class should be inheritted from and not used directly.
    """

    # Parent pipe, should only be used outside of the class
    pipe: Connection

    # Child pipe, should only be used inside of the class
    _pipe: Connection

    def __init__(self):
        """Establish a duplex IPC channel."""
        self.pipe, self._pipe = Pipe()


class _abstractMessage(ABC):
    """
    The base to build messages to send through a pipe.

    All messages sent through a Pipeable pipe should be inherited from this type.

    @NOTE This class should be inheritted from and not used directly.
    """

    def __init__(self, payload: Any):
        self.payload = payload

    def isType(self, classDeclaration: type) -> bool:
        """
        Whether the type of message is a certain type.

        Useful for determining which type of message before handling.

        >>> if myPipeableClass.pipe.poll():
        >>>     message = myPipeableClass.pipe.recv():
        >>>     if message.typeOf(StringMessage):
        >>>         print(message.payload)

        Args: classDeclaration (type): Comparison type

        Returns: bool: Whether the type of message is same as the comparison
            type
        """
        return self.__class__.__name__ == classDeclaration.__name__


class StringMessage(_abstractMessage):
    """A Pipeable message of type `str`."""

    def __init__(self, payload: str):
        """
        Create a message of type `str`.

        Args:
            payload (str): [description]
        """
        super().__init__(payload)


class LogMessage(_abstractMessage):
    """A Pipeable message to send logging information."""

    def __init__(self, payload: str, level: int = logging.INFO):
        """
        Create a message to send logging information.

        Args:
            payload (str): Log message
            level (int, optional): Logging level. Defaults to logging.INFO.
        """
        self.payload = payload
        self.level = level
