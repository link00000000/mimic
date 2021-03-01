import asyncio
import logging
from signal import SIGINT, SIGTERM, signal
from sys import stdout
from threading import Event, Thread

from mimic.GUI.GUI import GUI
from mimic.Logging.AsyncLoggingHandler import AsyncFileHandler
from mimic.Logging.TkinterLoggingHandler import TkinterTextHandler
from mimic.Pipeable import LogMessage, StringMessage
from mimic.TrayIcon import TrayIcon
from mimic.WebServer import WebServer

stop_event = Event()


def stop_handler(signal_number, frame):
    stop_event.set()


def run_server(server: WebServer):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(server.start())


def main():
    signal(SIGINT, stop_handler)
    signal(SIGTERM, stop_handler)

    tray_icon = TrayIcon(stop_event=stop_event)
    tray_icon.run()

    server = WebServer(stop_event=stop_event)
    server_thread = Thread(target=run_server, args=[server])
    server_thread.start()

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
        if server.pipe.poll():
            data = server.pipe.recv()

            if data.isType(LogMessage):
                level = data.level
                payload = data.payload

                if level is logging.DEBUG:
                    webserver_logger.debug(payload)
                elif level is logging.INFO:
                    webserver_logger.info(payload)
                elif level is logging.WARNING:
                    webserver_logger.warning(payload)
                elif level is logging.ERROR:
                    webserver_logger.error(payload)
                elif level is logging.CRITICAL:
                    webserver_logger.critical(payload)

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
