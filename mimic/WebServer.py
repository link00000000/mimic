"""
HTTP webserver with WebRTC video stream capabilities.

Only a single WebRTC video stream is allowed at a time. The video stream is
forwarded to pyvirtualcam.

After a ping message has not been sent for `_STALE_CONNECTION_TIMEOUT` seconds,
connections are automatically closed.

RTC data channels:
- latency - Ping messages are sent between the client and server periodically
  every `_PING_INTERVAL` seconds to make sure the connection is still alive and
  record round time time in
  milliseconds
- metadata - A single message is sent from the client during initial connection
  containing a JSON object with information about the video stream (see `MetaData`)
- 
"""

import asyncio
import json
import logging
import os
import ssl
import time
from json.decoder import JSONDecodeError
from multiprocessing.connection import Connection
from threading import Event
from typing import Awaitable, Callable, Optional

import pyvirtualcam
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import StreamResponse
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.exceptions import InvalidStateError
from aiortc.mediastreams import MediaStreamError
from aiortc.rtcdatachannel import RTCDataChannel
from aiortc.rtcpeerconnection import RemoteStreamTrack
from pyvirtualcam.camera import _WindowsCamera

from mimic.MetaData import MetaData
from mimic.Pipeable import LogMessage
from mimic.Utils.Host import resolve_host
from mimic.Utils.Time import RollingTimeout, latency, timestamp

ROOT = "mimic/public"
_STALE_CONNECTION_TIMEOUT = 5.0
_PING_INTERVAL = 1.0
_MAX_CAMERA_INIT_RETRY = 5
_CAMERA_INIT_RETRY_INTERVAL = 1

cam: Optional[_WindowsCamera] = None


async def start_web_server(stop_event: Event, pipe: Connection) -> None:
    """
    Set up and run the web server main loop.

    Server will gracefully shut down when `stop_event` flag is set.

    Args:
        stop_event (Event): A flag that, when true, will graceully shut down the server
        pipe (Connection): Pipe connection to receive information from server
    """
    # All active RTC peer connections
    pcs: set[RTCPeerConnection] = set()

    async def show_frame(track: RemoteStreamTrack) -> None:
        """
        Get a frame from a `RemoteStreamTrack` and paint it to the pyvirtualcam video buffer.

        Args:
            track (RemoteStreamTrack): Video track from WebRTC connection
        """
        frame = await track.recv()

        # Format is a 2d array containing an RGBA tuples
        # 640x480
        if cam is not None:
            frame_array = frame.to_ndarray(format="rgba")
            cam.send(frame_array)

        # @NOTE Not sure if we need this but I'm going to leave it in case we
        # ever need a case for it
        # cam.sleep_until_next_frame()

    def log(message: str, level: int = logging.INFO):
        """
        Send a log message through communication pipe.

        Args:
            message (str): Log message content
            level (int, optional): Logging level. Defaults to logging.INFO.
        """
        pipe.send(LogMessage(message, level))

    async def close_all_connections() -> int:
        """
        Close all open WebRTC connections and media streams.

        Returns:
            int: Number of connections that were closed
        """
        if cam is not None:
            cam.close()

        for pc in pcs:
            await pc.close()

        num_pcs = len(pcs)
        pcs.clear()

        return num_pcs

    # Rolling timeout that closes all peer connections after the client has not
    # responded for some time
    heartbeat_timeout = RollingTimeout(
        _STALE_CONNECTION_TIMEOUT, close_all_connections)

    @web.middleware
    async def logging_middleware(request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]) -> StreamResponse:
        """
        Send `LogMessage` through communication pipe for every HTTP request.

        Args:
            request (Request): HTTP request from http server
            handler ([type]): Handler to be executed after middleware

        Returns:
            StreamResponse: HTTP response after handler is executed
        """
        log(f"{request.method} {request.path} - {request.remote}", logging.DEBUG)
        return await handler(request)

    async def index(request: Request) -> StreamResponse:
        content = open(os.path.join(ROOT, "index.html"), "r").read()
        return web.Response(content_type="text/html", text=content)

    async def javascript(request: Request) -> StreamResponse:
        content = open(os.path.join(ROOT, "app.js"), "r").read()
        return web.Response(content_type="application/javascript", text=content)

    async def css(request: Request) -> StreamResponse:
        content = open(os.path.join(ROOT, "app.css"), "r").read()
        return web.Response(content_type="text/css", text=content)

    async def close(request: Request) -> StreamResponse:
        num_connections = await close_all_connections()
        return web.Response(text=f"Closed {num_connections} connection(s)")

    async def offer(request: Request) -> StreamResponse:
        params = await request.json()

        if params['sdp'] is None or params['type'] is None:
            return web.Response(status=400, text="Required `sdp` and `type` are missing from request body.")

        if len(pcs) != 0:
            return web.Response(status=409, text='Attempting to make more than one connection simultaneously. Resource busy.')

        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        pc = RTCPeerConnection()
        pcs.add(pc)

        log(f"Created for {request.remote}")

        @pc.on("datachannel")
        def on_datachannel(channel: RTCDataChannel):
            @channel.on("message")
            async def on_message(message):
                if isinstance(message, str):
                    if channel.label == 'latency':
                        # If we recieve a -1, then it is the first message
                        # and the rolling timout should be started
                        if message == '-1':
                            heartbeat_timeout.start()
                        else:
                            round_trip_time = latency(int(message))
                            log(f"Latency {round_trip_time}ms", logging.DEBUG)
                            heartbeat_timeout.rollback()

                        await asyncio.sleep(_PING_INTERVAL)
                        try:
                            channel.send(str(timestamp()))
                        except InvalidStateError:
                            # Theres a chance the server will try to send a
                            # message after the connection is closed,
                            # raising an `InvalidStateError`. We should just
                            # ignore those.
                            pass

                    if channel.label == 'metadata':
                        try:
                            metadata = MetaData(message)

                            try:
                                global cam
                                if cam is not None:
                                    cam.close()
                                    cam = None

                                log(f"Start camera with metadata: {metadata.width}x{metadata.height}@{metadata.framerate}",
                                    logging.DEBUG)

                                # HWND needs time to free before allocation of new camera
                                # See: https://github.com/link00000000/mimic/issues/41
                                for _ in range(_MAX_CAMERA_INIT_RETRY):
                                    try:
                                        cam = pyvirtualcam.Camera(
                                            metadata.width, metadata.height, metadata.framerate)
                                        break
                                    except RuntimeError as error:
                                        if error.args[0] != "error starting virtual camera output":
                                            raise error

                                        log("Failed to acquire camera, trying again...",
                                            logging.WARNING)

                                        # If we were unable to acquire the camera, wait for some time and try
                                        # again
                                        time.sleep(_CAMERA_INIT_RETRY_INTERVAL)

                                # If we could not acquire the camera after a few tries, raise an exception
                                if cam is None:
                                    raise RuntimeError(
                                        "error starting virtual camera output")

                            except RuntimeError as error:
                                log(str(error), logging.ERROR)
                                cam = None
                                await close_all_connections()

                        except (KeyError, TypeError, JSONDecodeError) as error:
                            log(str(error), logging.ERROR)
                            await close_all_connections()

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            log(f"Connection state is {pc.connectionState}")
            if pc.connectionState == "failed" or pc.connectionState == "closed":
                await pc.close()
                pcs.discard(pc)

        @pc.on("track")
        async def on_track(track: RemoteStreamTrack):
            log(f"Track {track.kind} received")

            if track.kind != "video":
                track.stop()
                return

            @track.on("ended")
            async def on_ended():
                log(f"Track {track.kind} ended")
                if cam is not None:
                    cam.close()

            while True:
                if track.readyState != "live":
                    break

                try:
                    await show_frame(track)
                except MediaStreamError as error:
                    if track.readyState == 'live':
                        raise error

        # handle offer
        await pc.setRemoteDescription(offer)

        # send answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
            ),
        )

    # Start HTTP server
    ssl_context = ssl.SSLContext()
    ssl_context.load_cert_chain(
        "certs/selfsigned.cert", "certs/selfsigned.pem")

    app = web.Application(middlewares=[logging_middleware])
    app.router.add_get("/", index)
    app.router.add_get("/app.js", javascript)
    app.router.add_get("/app.css", css)
    app.router.add_post("/offer", offer)
    app.router.add_get('/close', close)

    runner = web.AppRunner(app, handle_signals=True)
    await runner.setup()

    site = web.TCPSite(runner, host=resolve_host(),
                       port=8080, ssl_context=ssl_context)
    await site.start()

    log(f"Server listening at https://{resolve_host()}:8080")

    # Main loop
    while stop_event is None or not stop_event.is_set():
        await asyncio.sleep(0.05)

    # Clean up and close server
    if cam is not None:
        cam.close()

    await close_all_connections()
    await site.stop()
    await runner.shutdown()
    await runner.cleanup()
    await app.shutdown()
    await app.cleanup()


def webserver_thread_runner(stop_event: Event, pipe: Connection):
    """
    Initialize asyncio event loop and start web server.

    Typically be used as target for spawning threads or child processes.

    @NOTE The event loop must not already be running. It is likely that the
    event loop is already running on the mean thread if you are using asyncio.

    Args:
        stop_event (Event): A flag that, when true, will graceully shut down the server
        pipe (Connection): Pipe connection to receive information from server
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_exception_handler(lambda loop, context: print(loop, context))

    loop.run_until_complete(start_web_server(stop_event, pipe))
    print("DONE")
