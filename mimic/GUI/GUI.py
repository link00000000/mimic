import tkinter as tk

from mimic.EventEmitter import EventEmitter
from mimic.GUI.DebugLogWindow import DebugLogWindow
from mimic.GUI.MainWindow import MainWindow


class GUI(tk.Tk, EventEmitter):
    """
    Tkinter user interface instance
    """

    def __init__(self):
        super().__init__()

        self.create_windows()
        self.withdraw()

    def create_windows(self):
        """
        Initialize windows
        """
        self.debug_log_window = DebugLogWindow(self)
        self.main_window = MainWindow(self)
