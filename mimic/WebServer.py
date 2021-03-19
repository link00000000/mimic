import asyncio
import json
import logging
import os
import ssl
from multiprocessing.connection import Connection
from threading import Event

import pyvirtualcam
from aiohttp import web
from aiohttp.web_request import Request
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.rtcpeerconnection import RemoteStreamTrack
from av import VideoFrame

from mimic.Pipeable import LogMessage
from mimic.Utils.Host import resolve_host

ROOT = "mimic/public"

logger = logging.getLogger("pc")
pcs = set()


async def start_web_server(stop_event: Event, pipe: Connection):
    cam = pyvirtualcam.Camera(640, 480, 30)

    async def show_frame(track: RemoteStreamTrack) -> VideoFrame:
        frame = await track.recv()

        # Format is a 2d array containing an RGBA tuples
        # 640x480
        frame_array = frame.to_ndarray(format="rgba")
        frame_array[:, :, 3] = 255

        cam.send(frame_array)
        # cam.sleep_until_next_frame()

        return frame

    def log(message: str, level: int = logging.INFO):
        pipe.send(LogMessage(message, level))

    @web.middleware
    async def logging_middleware(request: Request, handler):
        log(f"{request.method} {request.path} - {request.remote}", logging.DEBUG)
        return await handler(request)

    async def index(request):
        content = open(os.path.join(ROOT, "index.html"), "r").read()
        return web.Response(content_type="text/html", text=content)

    async def javascript(request):
        content = open(os.path.join(ROOT, "app.js"), "r").read()
        return web.Response(content_type="application/javascript", text=content)

    async def css(request):
        content = open(os.path.join(ROOT, "app.css"), "r").read()
        return web.Response(content_type="text/css", text=content)

    async def offer(request):
        params = await request.json()
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        pc = RTCPeerConnection()
        pcs.add(pc)

        log(f"Created for {request.remote}")

        @pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(message):
                if isinstance(message, str) and message.startswith("ping"):
                    channel.send("pong" + message[4:])

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            log(f"Connection state is {pc.connectionState}")
            if pc.connectionState == "failed":
                await pc.close()
                pcs.discard(pc)

        @pc.on("track")
        async def on_track(track):
            log(f"Track {track.kind} received")

            if track.kind != "video":
                track.stop()
                return

            while True:
                if track.readyState != "live":
                    break

                await show_frame(track)

            @track.on("ended")
            async def on_ended():
                log(f"Track {track.kind} ended")

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

    async def shutdown():
        # close peer connections
        coros = [pc.close() for pc in pcs]
        await asyncio.gather(*coros)
        pcs.clear()

    ssl_context = ssl.SSLContext()
    ssl_context.load_cert_chain(
        "certs/selfsigned.cert", "certs/selfsigned.pem")

    app = web.Application(middlewares=[logging_middleware])
    app.router.add_get("/", index)
    app.router.add_get("/app.js", javascript)
    app.router.add_get("/app.css", css)
    app.router.add_post("/offer", offer)

    runner = web.AppRunner(app, handle_signals=True)
    await runner.setup()

    site = web.TCPSite(runner, host=resolve_host(),
                       port=8080, ssl_context=ssl_context)
    await site.start()

    log(f"Server listening at https://{resolve_host()}:8080")

    while stop_event is None or not stop_event.is_set():
        await asyncio.sleep(1)

    cam.close()

    await shutdown()
    await site.stop()
    await runner.shutdown()
    await runner.cleanup()
    await app.shutdown()
    await app.cleanup()


def webserver_thread_runner(stop_event: Event, pipe: Connection):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(start_web_server(stop_event, pipe))
