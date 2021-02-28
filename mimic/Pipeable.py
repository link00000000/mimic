import logging
from typing import Any
from multiprocessing import Pipe
from multiprocessing.connection import Connection
from abc import ABC


class Pipeable(ABC):
    """
    Allows for inter-process communication (IPC) from a class
    """
    pipe: Connection
    _pipe: Connection

    def __init__(self):
        self.pipe, self._pipe = Pipe()


class _abstractMessage():
    """
    All messages sent through a Pipeable pipe should be inherited from this type
    """

    def __init__(self, payload: Any):
        self.payload = payload

    def isType(self, classDeclaration: type) -> bool:
        """
        Whether the type of message is a certain type. Useful for determining
        which type of message before handling

        Args: classDeclaration (type): Comparison type

        Returns: bool: Whether the type of message is same as the comparison
            type
        """
        return self.__class__.__name__ == classDeclaration.__name__


class StringMessage(_abstractMessage):
    """
    A Pipeable message of type string
    """

    def __init__(self, payload: str):
        super().__init__(payload)


class LogMessage(_abstractMessage):
    """
    A Pipeable message to send logging information
    """

    def __init__(self, payload: str, level: int = logging.INFO):
        self.payload = payload
        self.level = level
