import asyncio
from Server import Server
from threading import Thread, Event
from signal import signal, SIGINT, SIGTERM

stop_event = Event()


def stop_handler(signal_number, frame):
    stop_event.set()


def run_server():
    server = Server(stop_event=stop_event)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(server.start())


def main():

    server_thread = Thread(target=run_server)
    server_thread.start()

    while True:
        signal(SIGINT, stop_handler)
        signal(SIGTERM, stop_handler)

        if stop_event.is_set():
            break

    server_thread.join()


if __name__ == "__main__":
    main()
