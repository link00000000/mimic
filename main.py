import asyncio

from aiohttp.web_request import Request
from Server import Server
from threading import Thread, Event
from signal import signal, SIGINT, SIGTERM
from EventEmitter import EventEmitter

stop_event = Event()


def stop_handler(signal_number, frame):
    stop_event.set()


def run_server(server: Server):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(server.start())


def main():
    server = Server(stop_event=stop_event)

    @server.on('start')
    def log_start():
        print("Web server is starting")

    @server.on('request')
    def log_request(path: str):
        print("Request made to", path)

    server_thread = Thread(target=run_server, args=[server])
    server_thread.start()

    while True:
        signal(SIGINT, stop_handler)
        signal(SIGTERM, stop_handler)

        if stop_event.is_set():
            break

    server_thread.join()


if __name__ == "__main__":
    main()
