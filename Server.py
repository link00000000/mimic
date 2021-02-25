from aiohttp import web
from aiohttp.web_request import Request
import asyncio
from threading import Event


class Server:
    host: str
    port: int

    routes = web.RouteTableDef()
    app = web.Application()

    stop_event: Event

    runner: web.AppRunner
    site: web.TCPSite

    def __init__(self, host='localhost', port=8080, stop_event: Event = None):
        self.host = host
        self.port = port

        self.stop_event = stop_event

    @routes.get('/')
    async def hello(request: Request):
        return web.Response(text="Hello, world")

    async def start(self):
        self.app.add_routes(self.routes)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, 'localhost', 8080)
        await self.site.start()

        print(f"aiohttp listening on http://{self.host}:{self.port}")

        # Loop infinitely in 1 hour intervals
        while True:
            if(self.stop_event != None and self.stop_event.is_set()):
                await self.runner.cleanup()
                return

            await asyncio.sleep(1)
