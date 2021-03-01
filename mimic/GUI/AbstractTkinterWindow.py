from abc import ABC
import tkinter as tk


class AbstractTkinterWindow(tk.Toplevel, tk.Frame, ABC):
    pass

    def hide(self):
        self.withdraw()

    def show(self):
        self.deiconify()
