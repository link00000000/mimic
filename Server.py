from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef
import asyncio
from typing import Callable


class Server:
    host: str
    port: int

    app = web.Application()
    runner: web.AppRunner
    site: web.TCPSite

    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port

    def add_route(self, route: AbstractRouteDef):
        self.app.add_routes([route])

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, 'localhost', 8080)
        await self.site.start()

        print(f"aiohttp listening on http://{self.host}:{self.port}")

        # Loop infinitely in 1 hour intervals
        while True:
            await asyncio.sleep(3600)
