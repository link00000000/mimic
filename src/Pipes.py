from typing import Any
from multiprocessing import Pipe


class Pipeable:
    pipe, _pipe = Pipe()


class _abstractMessage():
    def __init__(self, payload: Any):
        self.payload = payload

    def isType(self, classDeclaration: type) -> bool:
        return self.__class__.__name__ == classDeclaration.__name__


class StringMessage(_abstractMessage):
    def __init__(self, payload: str):
        super().__init__(payload)


def isType(instance: Any, classDeclaration: type):
    return instance.__class__.__name__ == classDeclaration.__name__
