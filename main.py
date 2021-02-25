import asyncio
from Server import Server
from threading import Thread


def run_server():
    server = Server()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(server.start())
    loop.run_forever()


def main():
    server_thread = Thread(target=run_server)
    server_thread.start()

    server_thread.join()


if __name__ == "__main__":
    main()
