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
"""

import asyncio
import json
import logging
import os
import ssl
from json.decoder import JSONDecodeError
from mimetypes import MimeTypes
from multiprocessing.connection import Connection
from threading import Event
from typing import Awaitable, Callable, Optional

import numpy as np
import pyvirtualcam
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import StreamResponse
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.exceptions import InvalidStateError
from aiortc.mediastreams import MediaStreamError
from aiortc.rtcdatachannel import RTCDataChannel
from aiortc.rtcpeerconnection import RemoteStreamTrack
from av import VideoFrame
from av.video.reformatter import VideoReformatter
from PIL import Image
from pyvirtualcam.camera import _WindowsCamera

from mimic.Constants import SLEEP_INTERVAL
from mimic.Pipeable import LogMessage
from mimic.Utils.AppData import mkdir_local_app_data, resolve_local_app_data
from mimic.Utils.Host import resolve_host
from mimic.Utils.SSL import generate_ssl_certs, ssl_certs_generated
from mimic.Utils.Time import RollingTimeout, latency, timestamp

ROOT = "mimic/public"
ASSETS_ROOT = "assets"

_STALE_CONNECTION_TIMEOUT = 5.0
_PING_INTERVAL = 1.0
_MAX_CAMERA_RETRY_COUNT = 5
_CAMERA_INIT_RETRY_INTERVAL = 1

_CAMERA_WIDTH = 1280
_CAMERA_HEIGHT = 720
_CAMERA_FPS = 30
_CAMERA_DELAY = 0

_MIMETYPES = MimeTypes()

cam: Optional[_WindowsCamera] = None
is_cam_idle = True

# Store a global referece to the reformatter for performance
# See https://pyav.org/docs/stable/api/video.html#av.video.reformatter.VideoReformatter
_VIDEO_REFORMATTER = VideoReformatter()

_NO_CAMREA_IMAGE_BMP = Image.open(os.path.join(ASSETS_ROOT, "no_camera.bmp")).convert('RGB')
_NO_CAMERA_IMAGE_FRAME = VideoFrame.from_ndarray(np.asanyarray(_NO_CAMREA_IMAGE_BMP, dtype=np.uint8), format="rgb24").reformat(
    width=_CAMERA_WIDTH, height=_CAMERA_HEIGHT, format='rgba')
_NO_CAMERA_IMAGE_NDARRAY = _NO_CAMERA_IMAGE_FRAME.to_ndarray()


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
            frame = _VIDEO_REFORMATTER.reformat(frame=frame, width=_CAMERA_WIDTH, height=_CAMERA_HEIGHT, format="rgba")
            cam.send(frame.to_ndarray())

        # @NOTE Not sure if we need this but I'm going to leave it in case we
        # ever need a case for it
        # cam.sleep_until_next_frame()

    def show_static_frame() -> None:
        """Paint static image to camera frame buffer."""
        if cam is None:
            raise RuntimeError('Trying to send frame to camera before initialization')

        cam.send(_NO_CAMERA_IMAGE_NDARRAY)

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
        global is_cam_idle
        is_cam_idle = True

        for pc in pcs.copy():
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

    async def static(request: Request) -> StreamResponse:
        filename = os.path.join(ROOT, request.match_info['filename'])

        if not os.path.exists(filename):
            return web.Response(status=404)

        content = open(filename, 'r').read()
        mime = _MIMETYPES.guess_type(filename)[0]
        return web.Response(text=content, content_type=mime)

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

                            global is_cam_idle
                            is_cam_idle = False
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

                global is_cam_idle
                is_cam_idle = True

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

    mkdir_local_app_data('certs')
    cert_file = resolve_local_app_data('certs', 'selfsigned.cert')
    key_file = resolve_local_app_data('certs', 'selfsigned.pem')

    if not ssl_certs_generated(cert_file, key_file):
        generate_ssl_certs(cert_file, key_file)

    ssl_context.load_cert_chain(cert_file, key_file)

    app = web.Application(middlewares=[logging_middleware])
    app.router.add_get("/", index)
    app.router.add_get(r'/{filename:.+}', static)
    app.router.add_post("/offer", offer)
    app.router.add_get('/close', close)

    runner = web.AppRunner(app, handle_signals=True)
    await runner.setup()

    site = web.TCPSite(runner, host=resolve_host(),
                       port=8080, ssl_context=ssl_context)
    await site.start()

    log(f"Server listening at https://{resolve_host()}:8080")

    # Acquire virtual camera
    camera_init_sucess = False
    for _ in range(_MAX_CAMERA_RETRY_COUNT):
        global cam
        try:
            cam = pyvirtualcam.Camera(_CAMERA_WIDTH, _CAMERA_HEIGHT, _CAMERA_FPS, _CAMERA_DELAY)
            camera_init_sucess = True
            break

        except RuntimeError as error:
            if error.args[0] != 'error starting virtual camera output':
                raise error

            log("Failed to acquire camera, retrying.", logging.WARN)
            await asyncio.sleep(_CAMERA_INIT_RETRY_INTERVAL)

    if not camera_init_sucess:
        raise RuntimeError("Failed to acquire camera.", logging.ERROR)

    # Main loop
    while stop_event is None or not stop_event.is_set():
        if is_cam_idle:
            show_static_frame()

        await asyncio.sleep(SLEEP_INTERVAL)

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
    loop.set_exception_handler(lambda loop, context: stop_event.set())

    loop.run_until_complete(start_web_server(stop_event, pipe))
