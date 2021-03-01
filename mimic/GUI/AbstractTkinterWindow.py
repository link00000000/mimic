"""Used my Mimic when creating new Tkinter windows."""
import tkinter as tk
from abc import ABC


class AbstractTkinterWindow(tk.Toplevel, tk.Frame, ABC):  # type: ignore
    """
    Abstract base class for Mimic Tkinter windows.

    Used to create new Tkinter windows by Mimic. Should be inheritted and not
    used directly.
    """

    pass

    def hide(self):
        """Hide the current window without destroying the reference."""
        self.withdraw()

    def show(self):
        """Show a hidden window from window reference."""
        self.deiconify()
