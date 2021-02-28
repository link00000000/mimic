import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import logging

from mimic.EventEmitter import EventEmitter


class GUI(tk.Frame, EventEmitter):
    """
    Tkinter user interface instance
    """

    widgets: list[tk.Widget] = []

    def __init__(self, master: tk.Tk = tk.Tk()):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

        # Gracefully exit when the close button ("x button") is clicked
        self.master.protocol("WM_DELETE_WINDOW", self.quit)

    def create_widgets(self):
        """
        Initialize widgets
        """

        # Logger text output
        self.debug_text = ScrolledText(self, state='disabled')
        self.debug_text.configure(font='TkFixedFont')
        self.grid(column=0, row=1, sticky='w', columnspan=4)
        self.debug_text.pack()

        self.hi_there = tk.Button(self)
        self.hi_there["text"] = "Hello, world!\n(Click me)"
        self.hi_there["command"] = self.say_hi
        self.hi_there.pack(side="top")

        self.close_btn = tk.Button(self, text="QUIT", fg="red",
                                   command=self.quit)
        self.close_btn.pack(side="bottom")

    def quit(self):
        """
        Cleanup and destroy GUI and emit a `quit` event
        """
        self.master.destroy()
        self._emit("quit")

    def say_hi(self):
        print("Hi there! 👋")
