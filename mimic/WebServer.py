"""HTTP web server."""
import asyncio
import logging
import os
from threading import Event
from typing import Any, Callable, Coroutine, Optional

from aiohttp import web
from aiohttp.web_app import Application
from aiohttp.web_request import Request

from mimic.Pipeable import LogMessage, Pipeable
from mimic.Utils import resolve_host

middleware = Callable[[Request, Any], Coroutine[Any, Any, Any]]


class WebServer(Pipeable):
    """
    Async HTTP server, messages can be recieved by polling `pipe`.

    @NOTE Because we need access to `self` inside the route, all routes
    must be defined inside of `__init__` instead of individual methods.
    """

    host: str
    port: int

    routes = web.RouteTableDef()
    middlewares: list[middleware] = []
    app: Application

    stop_event: Optional[Event]

    runner: web.AppRunner
    site: web.TCPSite

    def __init__(self, host: str = resolve_host(), port=8080, stop_event: Event = None):
        """
        Initialize web server.

        Args:
            host (str, optional): Host to listen to HTTP traffic on. Defaults to `resolve_host()`.
            port (int, optional): Port to listen to HTTP traffic on. Defaults to 8080.
            stop_event (Event, optional): When set, the web server will shutdown. Defaults to None.
        """
        super().__init__()

        self.host = host
        self.port = port

        self.stop_event = stop_event

        @web.middleware
        async def loggerMiddleware(request: Request, handler):
            self._pipe.send(LogMessage(f'{request.method} {request.path}'))

            return await handler(request)
        self.middlewares.append(loggerMiddleware)

        # Routes must be initialized inside the constructor so that we have access
        # to `self`
        @self.routes.get('/')
        async def index(request: Request):
            """
            Return public/index.html as entrypoint.
            """
            content: str
            with open(os.path.abspath("mimic/public/index.html"), "r") as file:
                content = file.read()

            return web.Response(content_type="text/html", text=content)

        @self.routes.get(r'/{filename:.+}')
        async def static(request: Request):
            """
            Return file contents of files located in public directory.

            If file is not found, return status code 404
            """
            filename = os.path.abspath(os.path.join(
                'mimic/public', request.match_info['filename']))

            if not os.path.exists(filename):
                return web.Response(status=404)

            with open(filename, "r") as file:
                content = file.read()

            return web.Response(text=content)

    async def start(self):
        """Start listening to HTTP traffic."""
        self._pipe.send(LogMessage("Web server starting..."))

        self.app = web.Application(middlewares=self.middlewares)
        self.app.add_routes(self.routes)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

        self._pipe.send(LogMessage(
            f"Web server listening at http://{resolve_host()}:{self.port}"))

        # Loop infinitely in 1 second intervals
        while True:
            # If the `stop_event` has been set, cleanup and close the HTTP
            # server
            if(self.stop_event != None and self.stop_event.is_set()):
                await self.runner.cleanup()
                return

            await asyncio.sleep(1)
