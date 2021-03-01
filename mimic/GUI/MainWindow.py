import tkinter as tk

from mimic.EventEmitter import EventEmitter
from mimic.GUI.AbstractTkinterWindow import AbstractTkinterWindow
from mimic.GUI.Widgets.QRCode import QRCodeImage
from mimic.Utils import resolve_host


class MainWindow(AbstractTkinterWindow, EventEmitter):
    widgets: list[tk.Widget] = []

    def __init__(self, master: tk.Tk):
        super().__init__(master)

        self.master = master
        self.create_widgets()

        # Gracefully exit when the close button ("x button") is clicked
        self.protocol("WM_DELETE_WINDOW", self.quit)

    def create_widgets(self):
        qr_code = QRCodeImage(self, f"http://{resolve_host()}:8080")
        qr_code.pack()

    def quit(self):
        """
        Cleanup and destroy GUI and emit a `quit` event
        """
        self.master.destroy()
        self._emit("quit")
