"""
Mimic allows you to use your mobile device as a remote webcam.

Copyright 2021

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import logging
import multiprocessing
import os
from multiprocessing import Event, Pipe, Process
from os import environ, mkdir
from signal import SIGINT, SIGTERM, signal
from sys import stdout
from time import sleep
from types import FrameType

from win32api import GetLastError
from win32event import CreateMutex
from winerror import ERROR_ALREADY_EXISTS

from mimic.Constants import SLEEP_INTERVAL
from mimic.GUI.GUI import GUI
from mimic.Logging.AsyncLoggingHandler import AsyncRotatingFileHanlder
from mimic.Logging.Formatter import log_formatter
from mimic.Logging.TkinterLoggingHandler import TkinterTextHandler
from mimic.Pipeable import LogMessage, StringMessage
from mimic.TrayIcon import TrayIcon
from mimic.Utils.AppData import (initialize_local_app_data,
                                 mkdir_local_app_data, resolve_local_app_data)
from mimic.Utils.Profiler import profile
from mimic.WebServer import webserver_thread_runner

stop_event = Event()


def stop_handler(signal_number: int, frame: FrameType) -> None:
    """
    Handle stop signal events.

    Args:
        signal_number (int): Signal number that originated the signal
        frame (FrameType): Current stack frame when signal was raised
    """
    stop_event.set()


def main() -> None:
    """Mimic main entrypoint."""
    signal(SIGINT, stop_handler)
    signal(SIGTERM, stop_handler)

    initialize_local_app_data()

    tray_icon = TrayIcon(icon_image="assets/favicon.ico",
                         hover_text="Mimic", stop_event=stop_event)
    tray_icon.run()

    webserver_pipe, remote_webserver_pipe = Pipe()
    server_process = Process(target=webserver_thread_runner, args=(
        stop_event, remote_webserver_pipe))
    server_process.start()

    gui = GUI()

    @gui.on('quit')
    def on_gui_quit():
        stop_event.set()

    # Initialize web server logger
    mkdir_local_app_data("logs")
    webserver_logger = logging.getLogger('mimic.webserver')

    _webserver_stdout_handler = logging.StreamHandler(stdout)
    _webserver_stdout_handler.setFormatter(log_formatter)
    _webserver_stdout_handler.setLevel(
        logging.DEBUG
        if "PY_ENV" in os.environ and os.environ["PY_ENV"] == "development"
        else logging.INFO
    )
    webserver_logger.addHandler(_webserver_stdout_handler)

    _webserver_file_handler = AsyncRotatingFileHanlder(resolve_local_app_data("logs", "webserver.log"))
    _webserver_file_handler.setFormatter(log_formatter)
    _webserver_file_handler.setLevel(logging.DEBUG)
    webserver_logger.addHandler(_webserver_file_handler)

    _webserver_tkinter_handler = TkinterTextHandler(gui.debug_log_window.debug_text)
    _webserver_tkinter_handler.setFormatter(log_formatter)
    _webserver_tkinter_handler.setLevel(
        logging.DEBUG
        if "PY_ENV" in os.environ and os.environ["PY_ENV"] == "development"
        else logging.INFO
    )
    webserver_logger.addHandler(_webserver_tkinter_handler)

    webserver_logger.setLevel(logging.DEBUG)

    # Main loop
    while True:
        if stop_event.is_set():
            break

        # Get data from web server
        if webserver_pipe.poll():
            data = webserver_pipe.recv()

            if data.isType(LogMessage):
                webserver_logger.log(data.level, data.payload)

        # Get data from tray icon
        if tray_icon.pipe.poll():
            message: StringMessage = tray_icon.pipe.recv()

            if message == "show_debug_logs":
                gui.debug_log_window.show()

            if message == "show_qr_code":
                gui.main_window.show()

        # Update GUI
        gui.update_idletasks()
        gui.update()

        sleep(SLEEP_INTERVAL)

    server_process.join()
    tray_icon.join()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    handle = CreateMutex(None, 1, "Mimic Mutex")

    if GetLastError() != ERROR_ALREADY_EXISTS:
        if "PY_ENV" in environ and environ["PY_ENV"] == "development":
            profile(main)
        else:
            main()
