from abc import ABC
from typing import Callable

from pythonlangutil.overload import Overload, signature


class EventEmitter(ABC):
    """
    An event system similar to Node's event system. Events are signalled by the
    class and listeners are invoked.
    """
    _listeners: dict[str, list[Callable]] = {}

    def _emit(self, event: str, *args, **kwargs):
        """
        Emit and event with an optional payload

        Args:
            event (str): Event type to emit on
            payload (Any | None): An optional payload to be sent with the event
        """
        if not event in self._listeners:
            return

        for emitter in self._listeners[event]:
            emitter(*args, **kwargs)

    @Overload
    @signature("str", "function")
    def on(self, event: str, callback: Callable[[any], None]):  # type: ignore
        """
        Listen to an event

        Args:
            event (str): Event type to listen to
            callback (Callable[[any], None]): Procedure executed when the event is fired
        """
        if not event in self._listeners:
            self._listeners[event] = []

        self._listeners[event].append(callback)

    @on.overload  # type: ignore
    @signature("str")
    def on(self, event: str):
        """
        Listen to an event.

        This is the decorator syntax for the `on` method. Execution is identical to `on`

        Usage:
            @on("myEvent")
            def handleMyEvent(eventPayload):
                print(eventPayload)

        Args:
            event (str): Event type to listen to
        """
        def decorator(func):
            return self.on(event, func)

        return decorator
