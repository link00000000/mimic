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

import asyncio
import logging
from signal import SIGINT, SIGTERM, signal
from sys import stdout
from threading import Event, Thread
from tkinter import TclError, Tk
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


# def run_server(server: WebServer):
def run_server(server):
    """
    Initialize and run the web server on a worker thread.

    Args:
        server (WebServer): Web server instance
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(server.start())


async def run_gui(root: Tk, interval=0.05):
    try:
        while True:
            root.update_idletasks()
            root.update()
            await asyncio.sleep(interval)

    except TclError as error:
        if "application has been destroyed" not in error.args[0]:
            raise error


def main():
    """Mimic main entrypoint."""
    signal(SIGINT, stop_handler)
    signal(SIGTERM, stop_handler)

    tray_icon = TrayIcon(stop_event=stop_event)
    tray_icon.run()

    # server = WebServer(stop_event=stop_event)
    server_thread = Thread(target=server_thread_runner, name="Web-Server")
    server_thread.start()

    gui = GUI()

    @gui.events.on('quit')
    def on_gui_quit():
        stop_event.set()

    # Initialize web server logger
    # webserver_logger = logging.getLogger('mimic.webserver')
    # webserver_logger.addHandler(AsyncFileHandler("mimic.log"))
    # webserver_logger.addHandler(logging.StreamHandler(stdout))
    # webserver_logger.addHandler(TkinterTextHandler(
    #     gui.debug_log_window.debug_text))
    # webserver_logger.setLevel(logging.DEBUG)

    # Main loop
    # while True:
    #     if stop_event.is_set():
    #         break

    # Get data from web server
    # if server.pipe.poll():
    #     data = server.pipe.recv()

    #     if data.isType(LogMessage):
    #         level = data.level
    #         payload = data.payload

    #         if level is logging.DEBUG:
    #             webserver_logger.debug(payload)
    #         elif level is logging.INFO:
    #             webserver_logger.info(payload)
    #         elif level is logging.WARNING:
    #             webserver_logger.warning(payload)
    #         elif level is logging.ERROR:
    #             webserver_logger.error(payload)
    #         elif level is logging.CRITICAL:
    #             webserver_logger.critical(payload)

    # Get data from tray icon
    # if tray_icon.pipe.poll():
    #     message: StringMessage = tray_icon.pipe.recv()

    #     if message == "show_debug_logs":
    #         gui.debug_log_window.show()

    # Update GUI
    # gui.update_idletasks()
    # gui.update()
    # await asyncio.gather(
    #     run_gui(gui),
    # )

    server_thread.join()


if __name__ == "__main__":
    main()
    # server_thread_runner()
    # event_loop = asyncio.get_event_loop()
    # event_loop.run_until_complete(main())
