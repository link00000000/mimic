import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from mimic.GUI.AbstractTkinterWindow import AbstractTkinterWindow
from mimic.Pipeable import Pipeable


class DebugLogWindow(AbstractTkinterWindow, Pipeable):
    def __init__(self, master: tk.Tk):
        super().__init__(master)

        self.master = master
        self.title("Mimic - Debug Logs")
        self.hide()

        self.create_widgets()

        self.protocol("WM_DELETE_WINDOW", self.hide)

    def create_widgets(self):
        # Logger text output
        self.debug_text = ScrolledText(self, state='disabled')
        self.debug_text.configure(font='TkFixedFont')
        self.debug_text.pack()
