import asyncio
import json
import logging
import os
import ssl
from mimetypes import MimeTypes
from multiprocessing.connection import Connection
from threading import Event
from typing import Any, Awaitable, Callable, Coroutine

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response, StreamResponse
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.rtcdatachannel import RTCDataChannel

from mimic.Pipeable import LogMessage
from mimic.Utils.Host import resolve_host

PUBLIC_ROOT = os.path.abspath('mimic/public')
MIME_TYPES = MimeTypes()

middleware = Callable[[Request, Any], Coroutine[Any, Any, Any]]
route_handler = Callable[[Request], Awaitable[Response]]


class WebServer:
    __pcs: set[RTCPeerConnection] = set()
    __routes = web.RouteTableDef()
    __middlewares: list[middleware] = []

    def __init__(self, host: str = resolve_host(), port: int = 8080, pipe: Connection = None, stop_event: Event = Event()) -> None:
        self.__host = host
        self.__port = port
        self.__pipe = pipe
        self.__stop_event = stop_event

        @self.__middleware
        @web.middleware
        async def loggerMiddleware(request: Request, handler: route_handler) -> StreamResponse:
            self.__log(f"{request.method} {request.path} - {request.remote}")
            return await handler(request)

        @self.__routes.get('/')
        async def index(request: Request) -> StreamResponse:
            content = open(os.path.join(PUBLIC_ROOT, "index.html"), "r").read()
            return web.Response(content_type="text/html", text=content)

        @self.__routes.get('/close')
        async def close_connection(request: Request) -> StreamResponse:
            for pc in self.__pcs:
                await pc.close()

            num_pcs = len(self.__pcs)
            self.__pcs.clear()

            return web.Response(text=f"Closed {num_pcs} connection(s)", status=200)

        @self.__routes.post('/webrtc-offer')
        async def offer(request: Request) -> StreamResponse:
            request_body = await request.json()

            if request_body['sdp'] is None or request_body['type'] is None:
                return web.Response(status=400, text="Bad request, must include 'sdp' and 'type'.")

            offer = RTCSessionDescription(
                sdp=request_body["sdp"], type=request_body["type"])

            pc = RTCPeerConnection()
            self.__pcs.add(pc)

            self.__log(f"Connection created for {request.remote}")

            @pc.on("datachannel")
            def on_datachannel(channel: RTCDataChannel) -> None:
                @channel.on("message")
                def on_message(message: Any) -> None:
                    if isinstance(message, str) and message.startswith("ping"):
                        channel.send("pong" + message[4:])

            @pc.on("connectionstatechange")
            async def on_connectionstatechange() -> None:
                self.__log(
                    f"Connection state is {pc.connectionState}", logging.DEBUG)
                if pc.connectionState == "failed":
                    await pc.close()
                    self.__pcs.discard(pc)

            @pc.on("track")
            def on_track(track: MediaStreamTrack) -> None:
                self.__log(f"Track {track.kind} received", logging.DEBUG)

                @track.on("ended")
                async def on_ended() -> None:
                    self.__log(f"Track {track.kind} ended", logging.DEBUG)

            # handle offer
            await pc.setRemoteDescription(offer)

            # send answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            return web.Response(
                content_type="application/json",
                text=json.dumps(
                    {"sdp": pc.localDescription.sdp,
                        "type": pc.localDescription.type}
                ),
            )

        @self.__routes.get(r'/{filename:.+}')
        async def static(request: Request) -> StreamResponse:
            filename = os.path.join(
                PUBLIC_ROOT, request.match_info['filename'])

            if not os.path.exists(filename):
                return web.Response(status=404)

            content = open(filename, "r").read()

            mime = MIME_TYPES.guess_type(filename)[0]
            return web.Response(content_type=mime, text=content)

    def __log(self, message: str, level: int = logging.INFO) -> None:
        if self.__pipe is None:
            print(message)

        else:
            self.__pipe.send(LogMessage(message, level))

    def __middleware(self, func: Callable) -> Callable:
        self.__middlewares.append(func)
        return func

    async def __on_shutdown(self) -> None:
        # close peer connections
        coros = [pc.close() for pc in self.__pcs]
        await asyncio.gather(*coros)
        self.__pcs.clear()

    async def start(self) -> None:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(
            "./certs/selfsigned.cert", "./certs/selfsigned.pem")

        app = web.Application(middlewares=self.__middlewares)
        app.router.add_routes(self.__routes)

        runner = web.AppRunner(app, handle_signals=True)
        await runner.setup()

        site = web.TCPSite(runner, self.__host, self.__port,
                           ssl_context=ssl_context)
        await site.start()

        print(f"Listening at https://{self.__host}:{self.__port}")

        while not self.__stop_event.is_set():
            await asyncio.sleep(1)

        await self.__on_shutdown()
        await runner.cleanup()


def server_thread_runner(pipe: Connection, stop_event: Event) -> None:
    """Initialize and run the web server on a worker thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    server = WebServer(pipe=pipe, stop_event=stop_event)

    loop.run_until_complete(server.start())
