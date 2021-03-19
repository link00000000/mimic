import asyncio
import json
import logging
import os
import ssl
from multiprocessing.connection import Connection
from threading import Event
from typing import Optional

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
from pyvirtualcam.camera import _WindowsCamera

from mimic.Pipeable import LogMessage
from mimic.Utils.Host import resolve_host
from mimic.Utils.Time import RollingTimeout, latency, timestamp

ROOT = "mimic/public"
_STALE_CONNECTION_TIMEOUT = 5.0
_PING_INTERVAL = 1.0

cam: Optional[_WindowsCamera] = None


async def start_web_server(stop_event: Event, pipe: Connection) -> None:
    pcs: set[RTCPeerConnection] = set()

    async def show_frame(track: RemoteStreamTrack) -> VideoFrame:
        frame = await track.recv()

        # Format is a 2d array containing an RGBA tuples
        # 640x480
        if cam is not None:
            frame_array = frame.to_ndarray(format="rgba")
            cam.send(frame_array)

        # @NOTE Not sure if we need this but I'm going to leave it in case we
        # ever need a case for it
        # cam.sleep_until_next_frame()

        return frame

    def log(message: str, level: int = logging.INFO):
        pipe.send(LogMessage(message, level))

    async def close_all_connections() -> int:
        if cam is not None:
            cam.close()

        for pc in pcs:
            await pc.close()

        num_pcs = len(pcs)
        pcs.clear()

        return num_pcs

    heartbeat_timeout = RollingTimeout(
        _STALE_CONNECTION_TIMEOUT, close_all_connections)

    @web.middleware
    async def logging_middleware(request: Request, handler) -> StreamResponse:
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

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            log(f"Connection state is {pc.connectionState}")
            if pc.connectionState == "failed":
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

            global cam
            cam = pyvirtualcam.Camera(640, 480, 30)

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

    while stop_event is None or not stop_event.is_set():
        await asyncio.sleep(0.05)

    if cam is not None:
        cam.close()

    await close_all_connections()
    await site.stop()
    await runner.shutdown()
    await runner.cleanup()
    await app.shutdown()
    await app.cleanup()


def webserver_thread_runner(stop_event: Event, pipe: Connection):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(start_web_server(stop_event, pipe))
