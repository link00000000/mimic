from mimic.Pipeable import Pipeable
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from mimic.EventEmitter import EventEmitter


class _TkinterWindow(tk.Toplevel, tk.Frame):
    pass

    def hide(self):
        self.withdraw()

    def show(self):
        self.deiconify()


class DebugLog(_TkinterWindow, Pipeable):
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


class MainWindow(_TkinterWindow, EventEmitter):
    widgets: list[tk.Widget] = []

    def __init__(self, master: tk.Tk):
        super().__init__(master)

        self.master = master
        self.create_widgets()

        # Gracefully exit when the close button ("x button") is clicked
        self.protocol("WM_DELETE_WINDOW", self.quit)

    def create_widgets(self):
        self.hi_there = tk.Button(self)
        self.hi_there["text"] = "Hello, world!\n(Click me)"
        self.hi_there["command"] = self.say_hi
        self.hi_there.pack(side="top")

        self.close_btn = tk.Button(self, text="QUIT", fg="red",
                                   command=self.quit)
        self.close_btn.pack(side="bottom")

    def say_hi(self):
        print("Hi there! 👋")

    def quit(self):
        """
        Cleanup and destroy GUI and emit a `quit` event
        """
        print("QUITTING")
        self.master.destroy()
        self._emit("quit")


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
        self.debug_log_window = DebugLog(self)
        self.main_window = MainWindow(self)
