import tkinter as tk
from abc import ABC


class AbstractTkinterWindow(tk.Toplevel, tk.Frame, ABC):  # type: ignore
    pass

    def hide(self):
        self.withdraw()

    def show(self):
        self.deiconify()
