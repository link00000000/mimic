"""Mimic main window."""
import tkinter as tk

from mimic.EventEmitter import EventEmitter
from mimic.GUI.AbstractTkinterWindow import AbstractTkinterWindow
from mimic.GUI.Widgets.QRCode import QRCodeImage
from mimic.Utils.Host import resolve_host


class MainWindow(AbstractTkinterWindow, EventEmitter):
    """Mimic main window."""

    widgets: list[tk.Widget] = []

    def __init__(self, master: tk.Tk):
        """
        Attaches main window to the main Tkinter instance.

        Should only pass the amin Tkinter instance as the `master`.
        I don't knwo what will happen if we try to nest windows inside
        eachother.

        Args:
            master (tk.Tk): Master Tkinter instance
        """
        super().__init__(master)

        self.master = master
        self.create_widgets()

        # Gracefully exit when the close button ("x button") is clicked
        self.protocol("WM_DELETE_WINDOW", self.quit)

    def create_widgets(self):
        """Register widgets to window."""
        qr_code = QRCodeImage(self, f"https://{resolve_host()}:8080")
        qr_code.pack()

    def quit(self):
        """
        Destory GUI and emit `quit`.

        Cleanup and gracefully destory master Tkinter instance and emit
        a `quit` event.
        """
        self.master.destroy()
        self._emit("quit")
