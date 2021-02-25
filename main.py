import asyncio
from Server import Server
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import StreamResponse
from typing import Awaitable


async def hello_world_handler(request: Request) -> Awaitable[StreamResponse]:
    return web.Response(text="👋,🌎!")


def main():
    server = Server()
    server.add_route(web.get('/', hello_world_handler))

    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(server.start())


if __name__ == "__main__":
    main()
