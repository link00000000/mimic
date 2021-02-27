from aiohttp import web
from aiohttp.web_request import Request
import asyncio
from threading import Event
from mimic.Pipeable import StringMessage, Pipeable


class Server(Pipeable):
    """
    Async HTTP server, messages can be recieved by polling `pipe`.

    @NOTE: Because we need access to `self` inside the route, all routes
    must be defined inside of `__init__` instead of individual methods.
    """

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

        @self.routes.get('/')
        async def hello(request: Request):
            self._pipe.send(StringMessage("GET /"))
            return web.Response(text="Hello, world")

    async def start(self):
        """
        Start listening to HTTP traffic
        """
        self._pipe.send(StringMessage("Web server starting..."))

        self.app.add_routes(self.routes)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

        print(f"aiohttp listening on http://{self.host}:{self.port}")

        # Loop infinitely in 1 second intervals
        while True:
            # If the `stop_event` has been set, cleanup and close the HTTP
            # server
            if(self.stop_event != None and self.stop_event.is_set()):
                await self.runner.cleanup()
                return

            await asyncio.sleep(1)
