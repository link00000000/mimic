"""Mimic debug window that shows the current logs."""
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from mimic.GUI.AbstractTkinterWindow import AbstractTkinterWindow
from mimic.Pipeable import Pipeable
from PIL import Image, ImageTk


class DebugLogWindow(AbstractTkinterWindow, Pipeable):
    """Mimic debug window that shows the current logs."""

    def __init__(self, master: tk.Tk):
        """
        Attaches a debug window to the main Tkinter instance.

        Should only pass the main Tkinter instance as the `master`.
        I don't know what will happen if we try to nest windows inside
        eachother.

        Args:
            master (tk.Tk): Master Tkinter instance
        """
        super().__init__(master)

        self.master = master

        # TkInter photoimage only supports PPM PGM image formats
        # Using ImageTk and Image from PIL gets around this
        mimic_logo = ImageTk.PhotoImage(Image.open("./assets/favicon.ico"))
        self.iconphoto(False, mimic_logo)

        self.title("Mimic - Debug Logs")
        self.hide()

        self.create_widgets()

        # Instead of destroying the window reference on close, we should just
        # hide it and keep a reference to it so it can continue to recieve logging
        # messages and re-render if opened again
        self.protocol("WM_DELETE_WINDOW", self.hide)

    def create_widgets(self):
        """Register widgets to window."""
        # The text from the logger, is registerd as a logger handler in
        # the main process
        self.debug_text = ScrolledText(self, state='disabled')
        self.debug_text.configure(font='TkFixedFont')
        self.debug_text.pack()
