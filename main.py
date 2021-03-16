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
from multiprocessing.connection import Pipe
from signal import SIGINT, SIGTERM, signal
from sys import stdout
from threading import Event, Thread
from types import FrameType

from mimic.GUI.GUI import GUI
from mimic.Logging.AsyncLoggingHandler import AsyncFileHandler
from mimic.Logging.TkinterLoggingHandler import TkinterTextHandler
from mimic.Pipeable import LogMessage, StringMessage
from mimic.TrayIcon import TrayIcon
from mimic.WebServer import server_thread_runner

stop_event = Event()


def stop_handler(signal_number: int, frame: FrameType):
    """
    Handle stop signal events.

    Args:
        signal_number (int): Signal number that originated the signal
        frame (FrameType): Current stack frame when signal was raised
    """
    stop_event.set()


def main():
    """Mimic main entrypoint."""
    signal(SIGINT, stop_handler)
    signal(SIGTERM, stop_handler)

    tray_icon = TrayIcon(stop_event=stop_event)
    tray_icon.run()

    server_pipe, _server_pipe = Pipe()
    server_thread = Thread(target=server_thread_runner, args=[
                           _server_pipe], name="WebServer")
    server_thread.start()

    gui = GUI()

    @gui.events.on('quit')
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
    while not stop_event.is_set():

        # Get data from web server
        if server_pipe.poll():
            data: LogMessage = server_pipe.recv()
            webserver_logger.log(data.level, data.payload)

        # Get data from tray icon
        if tray_icon.pipe.poll():
            message: StringMessage = tray_icon.pipe.recv()

            if message == "show_debug_logs":
                gui.debug_log_window.show()

        # Update GUI
        gui.update_idletasks()
        gui.update()

    server_thread.join()


if __name__ == "__main__":
    main()
