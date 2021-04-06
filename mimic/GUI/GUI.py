"""Main GUI entrypoint."""
import tkinter as tk

from mimic.EventEmitter import EventEmitter
from mimic.GUI.DebugLogWindow import DebugLogWindow
from mimic.GUI.MainWindow import MainWindow
from PIL import Image, ImageTk


class GUI(tk.Tk, EventEmitter):
    """Main Tkinter user interface instance."""

    def __init__(self):
        """Initialize main Tkinter user interface instance."""
        super().__init__()

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

        # TkInter photoimage only supports PPM PGM image formats
        # Using ImageTk and Image from PIL gets around this
        mimic_logo = ImageTk.PhotoImage(Image.open("./assets/favicon.ico"))
        self.debug_log_window.iconphoto(False, mimic_logo)
        self.main_window.iconphoto(False, mimic_logo)
