"""Mimic's system tray icon."""
from threading import Event, Thread
from typing import Callable, Optional

from infi.systray import SysTrayIcon

from mimic.Pipeable import Pipeable


class TrayIcon(Pipeable):
    """
    Non-blocking tray icon.

    Tray icons require blocking due to having to wait for button clicks.
    To prevent blocking on the main thread, a tread is spawned for the tray
    icon and click events are send through `Pipeable` pipes.
    """

    MenuOptionCallback = Callable[[SysTrayIcon], None]
    MenuOption = tuple[str, Optional[str], MenuOptionCallback]

    _thread: Thread
    _icon: SysTrayIcon
    _menu_options: list[MenuOption] = []
    _stop_event: Event

    _icon_image: str
    _hover_text: str

    def __init__(self, icon_image: str = "icon.ico", hover_text: str = "Hover text", stop_event: Event = Event()):
        """
        Initialize system tray icon.

        Args:
            icon_image (str, optional): Name of image to use as tray icon. Defaults to "icon.ico".
            hover_text (str, optional): Text displayed when the tray icon is hovered. Defaults to "Hover text".
            stop_event (Event, optional): Flag is set when the tray icon process exits. Defaults to Event().
        """
        super().__init__()

        self._stop_event = stop_event

        self._icon_image = icon_image
        self._hover_text = hover_text

        self._menu_options = [
            ("Show debug logs", None, lambda icon: self._pipe.send("show_debug_logs"))
        ]

    def run(self):
        """
        Display the tray icon in the system tray.

        Tray icon thread is spawned and the tray loop is executed.
        """
        self._icon = SysTrayIcon(
            self._icon_image, self._hover_text, tuple(self._menu_options), on_quit=self.handle_quit)

        self._thread = Thread(target=self._loop, name="TrayIcon")
        self._thread.start()

    def handle_quit(self, icon: SysTrayIcon):
        """
        Set the stop flag.

        Called when the quit option is selected from the icons context menu.

        Args:
            icon (SysTrayIcon): SysTrayIcon reference
        """
        self._stop_event.set()

    def _loop(self):
        """
        Listen to events on the system tray icon.

        @NOTE This should not be run directly and will block the main thread.
        It is automatically executed on a spawned worker thread internally.
        """
        self._icon.start()

        while True:
            if self._stop_event.is_set():
                self._icon.shutdown()
                return
