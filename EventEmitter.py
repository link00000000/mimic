from typing import Callable
from pythonlangutil.overload import Overload, signature


class EventEmitter:
    _listeners: dict[str, list[Callable]] = {}

    def _emit(self, event: str, *args, **kwargs):
        if not event in self._listeners:
            return

        for emitter in self._listeners[event]:
            emitter(*args, **kwargs)

    @Overload
    @signature("str", "function")
    def on(self, event: str, callback: Callable[[any], None]):
        if not event in self._listeners:
            self._listeners[event] = []

        self._listeners[event].append(callback)

    @on.overload
    @signature("str")
    def on(self, event: str):
        def decorator(func):
            return self.on(event, func)

        return decorator
