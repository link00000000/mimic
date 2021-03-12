"""Main GUI entrypoint."""
import tkinter as tk

from mimic.GUI.DebugLogWindow import DebugLogWindow
from mimic.GUI.MainWindow import MainWindow
from pyee import BaseEventEmitter


class GUI(tk.Tk):
    """Main Tkinter user interface instance."""

    events = BaseEventEmitter()

    def __init__(self):
        """Initialize main Tkinter user interface instance."""
        super().__init__()
        super(BaseEventEmitter).__init__()

        self.create_windows()

        # The main Tkinter instance will spawn a window. Instead of using this
        # window, we want to spawn child windows off of it and use them instead
        # and use the main window to coordinate the other windows. Because we
        # don't want this main window to be displayed, we hide it.
        self.withdraw()

    def create_windows(self):
        """Initialize all child windows."""
        self.debug_log_window = DebugLogWindow(self)
        self.main_window = MainWindow(self)

        @self.main_window.events.on('quit')
        def on_quit():
            self.events.emit('quit')
