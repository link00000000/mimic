"""HTTP web server."""
import asyncio
import json
import os
import ssl
import time
from mimetypes import MimeTypes
from threading import Event
from typing import Any, Callable, Coroutine, Optional

from aiohttp import web
from aiohttp.web_app import Application
from aiohttp.web_request import Request
from aiortc import RTCSessionDescription
from aiortc.rtcpeerconnection import RTCPeerConnection

from mimic.Pipeable import LogMessage, Pipeable
from mimic.Utils.Host import resolve_host
from mimic.Utils.SSL import generate_ssl_certs, ssl_certs_generated
from mimic.WebRTCVideoStream import WebRTCVideoStream

middleware = Callable[[Request, Any], Coroutine[Any, Any, Any]]
mimetypes = MimeTypes()

# Certificates can be generated with `pipenv run ssl_gencerts`
SSL_CERT = "certs/selfsigned.cert"
SSL_KEY = "certs/selfsigned.pem"


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

    peer_connections: set[RTCPeerConnection] = set()

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
            """Return public/index.html as entrypoint."""
            content: str
            with open(os.path.abspath("mimic/public/index.html"), "r") as file:
                content = file.read()

            return web.Response(content_type="text/html", text=content)

        @self.routes.post('/webrtc-offer')
        async def offer(request):
            if len(self.peer_connections) != 0:
                return web.Response(status=409, text="Active connection already in use.")

            params = await request.json()
            offer = RTCSessionDescription(
                sdp=params["sdp"], type=params["type"])

            peer_connection = RTCPeerConnection()
            self.peer_connections.add(peer_connection)

            @peer_connection.on("datachannel")
            def on_datachannel(channel):
                @channel.on("message")
                def on_message(message):
                    if isinstance(message, str) and message.startswith("ping"):
                        channel.send("pong" + message[4:])

            @peer_connection.on("connectionstatechange")
            async def on_connectionstatechange():
                print("Connection state is", peer_connection.connectionState)
                if peer_connection.connectionState == "failed":
                    await peer_connection.close()
                    self.peer_connections.discard(peer_connection)

            @peer_connection.on("track")
            def on_track(track):
                print(f"Track {track.kind} received")

                if track.kind == "audio":
                    print("Got audio track")
                elif track.kind == "video":
                    print(f"Got other track {track.kind}")

                @track.on("ended")
                async def on_ended():
                    print(f"Track {track.kind} ended")

            # handle offer
            await peer_connection.setRemoteDescription(offer)

            # send answer
            answer = await peer_connection.createAnswer()
            await peer_connection.setLocalDescription(answer)

            return web.Response(
                content_type="application/json",
                text=json.dumps(
                    {"sdp": peer_connection.localDescription.sdp,
                        "type": peer_connection.localDescription.type}
                ),
            )

        @self.routes.get(r'/{filename:.+}')
        async def static(request: Request):
            """
            Return file contents of files located in public directory.

            If file is not found, return status code 404. Mime type of file is
            guessed based off of file extension.
            """
            filename = os.path.abspath(os.path.join(
                'mimic/public', request.match_info['filename']))

            if not os.path.exists(filename):
                return web.Response(status=404)

            with open(filename, "r") as file:
                content = file.read()

            mime = mimetypes.guess_type(filename)[0]
            return web.Response(content_type=mime, text=content)

    async def start(self):
        """Start listening to HTTP traffic."""
        self._pipe.send(LogMessage("Web server starting..."))

        self.app = web.Application(middlewares=self.middlewares)
        self.app.add_routes(self.routes)

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        if not ssl_certs_generated(SSL_CERT, SSL_KEY):
            self._pipe.send(LogMessage(
                "SSL certificate and key not found! Generating SSL certificate and key..."))
            generate_ssl_certs(SSL_CERT, SSL_KEY)
            self._pipe.send(LogMessage("SSL certificate and key generated."))
        else:
            self._pipe.send(LogMessage("SSL certificate and key found."))

        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(SSL_CERT, SSL_KEY)

        self.site = web.TCPSite(self.runner, self.host,
                                self.port, ssl_context=ssl_context)
        await self.site.start()

        self._pipe.send(LogMessage(
            f"Web server listening at https://{resolve_host()}:{self.port}"))

        # Loop infinitely in 1 second intervals
        while True:
            # If the `stop_event` has been set, cleanup and close the HTTP
            # server
            if(self.stop_event != None and self.stop_event.is_set()):
                await self.runner.cleanup()
                return

            await asyncio.sleep(1)
