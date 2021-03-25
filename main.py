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
from multiprocessing import Event, Pipe, Process
from signal import SIGINT, SIGTERM, signal
from sys import stdout
from types import FrameType

from mimic.GUI.GUI import GUI
from mimic.Logging.AsyncLoggingHandler import AsyncFileHandler
from mimic.Logging.TkinterLoggingHandler import TkinterTextHandler
from mimic.Pipeable import LogMessage, StringMessage
from mimic.TrayIcon import TrayIcon
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

    tray_icon = TrayIcon(hover_text="Mimic", stop_event=stop_event)
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
    webserver_logger = logging.getLogger('mimic.webserver')
    webserver_logger.addHandler(AsyncFileHandler("mimic.log"))
    webserver_logger.addHandler(logging.StreamHandler(stdout))
    webserver_logger.addHandler(TkinterTextHandler(
        gui.debug_log_window.debug_text))
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

    server_process.join()


if __name__ == "__main__":
    main()
