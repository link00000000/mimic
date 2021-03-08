"""Logging to Tkinter.Text widget for Python's built-in logging library."""
import logging
import tkinter as tk


class TkinterTextHandler(logging.Handler):
    """Register Tkinter.Text as logging handler."""

    def __init__(self, text: tk.Text):
        """
        Register Tkinter.Text element as logging handler.

        Args:
            text (tk.Text): Tkinter.Text element to render logs to
        """
        logging.Handler.__init__(self)
        self.text = text
        self.formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')

    def emit(self, record: logging.LogRecord):
        """
        Render new log message to Tkinter Text element.

        Called when a new message is logged.

        @NOTE Should *not* be called directly, called by Python's logging
        library.

        Args:
            record (logging.LogRecord): New log message
        """
        message = self.format(record)

        self.text.configure(state='normal')
        self.text.insert(tk.END, message + '\n')
        self.text.configure(state='disabled')

        self.text.yview(tk.END)
