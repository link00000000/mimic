import logging
import asyncio
from threading import Thread, Event
from signal import signal, SIGINT, SIGTERM

from mimic.GUI import GUI
from mimic.WebServer import WebServer
from mimic.Pipeable import LogMessage
from mimic.AsyncLoggingHandler import AsyncFileHandler

stop_event = Event()


def stop_handler(signal_number, frame):
    stop_event.set()


def run_server(server: WebServer):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(server.start())


def run_gui(app: GUI):
    app.mainloop()


def main():
    signal(SIGINT, stop_handler)
    signal(SIGTERM, stop_handler)

    server = WebServer(stop_event=stop_event)
    server_thread = Thread(target=run_server, args=[server])
    server_thread.start()

    gui = GUI()

    @gui.on('quit')
    def on_gui_quit():
        print("Stopping...")
        stop_event.set()

    webserver_logger = logging.getLogger('mimic.webserver')
    webserver_logger.addHandler(AsyncFileHandler("mimic.log"))

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

        # Update GUI
        gui.update_idletasks()
        gui.update()

    server_thread.join()


if __name__ == "__main__":
    main()
