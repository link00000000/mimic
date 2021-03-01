from threading import Event, Thread
from typing import Callable

from infi.systray import SysTrayIcon

from mimic.Pipeable import Pipeable


class TrayIcon(Pipeable):
    _thread: Thread
    _icon: SysTrayIcon
    _menu_options: list[tuple[str, str, Callable[[SysTrayIcon], None]]] = []
    _stop_event: Event

    _icon_image: str
    _hover_text: str

    def __init__(self, icon_image: str = "icon.ico", hover_text: str = "Hover text", stop_event: Event = Event()):
        super().__init__()

        self._stop_event = stop_event

        self._icon_image = icon_image
        self._hover_text = hover_text

        self._menu_options = [
            ("Show debug logs", None, lambda icon: self._pipe.send("show_debug_logs"))
        ]

    def run(self):
        self._icon = SysTrayIcon(
            self._icon_image, self._hover_text, tuple(self._menu_options), on_quit=self.handle_quit)

        self._thread = Thread(target=self._loop)
        self._thread.start()

    def handle_quit(self, icon: SysTrayIcon):
        self._stop_event.set()

    def _loop(self):
        self._icon.start()

        while True:
            if self._stop_event.is_set():
                self._icon.shutdown()
                return
