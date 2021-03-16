import asyncio
import json
import logging
import os
import ssl
import uuid
from threading import Thread

from aiohttp import web
from aiohttp.web_request import Request
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription

from mimic.Utils.Host import resolve_host

ROOT = os.path.abspath('mimic/public')


class WebServer:
    logger = logging.getLogger("pc")
    pcs: set[RTCPeerConnection] = set()
    routes = web.RouteTableDef()

    def __init__(self, host=resolve_host(), port=8080) -> None:
        self.host = host
        self.port = port

        @self.routes.get('/')
        async def index(request):
            content = open(os.path.join(ROOT, "index.html"), "r").read()
            return web.Response(content_type="text/html", text=content)

        @self.routes.get('/app.js')
        async def javascript(request):
            content = open(os.path.join(ROOT, "app.js"), "r").read()
            return web.Response(content_type="application/javascript", text=content)

        @self.routes.get('/app.css')
        async def css(request):
            content = open(os.path.join(ROOT, "app.css"), "r").read()
            return web.Response(content_type="text/css", text=content)

        @self.routes.get('/close')
        async def close_connection(request: Request):
            for pc in self.pcs:
                await pc.close()

            num_pcs = len(self.pcs)
            self.pcs.clear()

            return web.Response(text=f"Closed {num_pcs} connection(s)", status=200)

        @self.routes.post('/webrtc-offer')
        async def offer(request):
            params = await request.json()
            offer = RTCSessionDescription(
                sdp=params["sdp"], type=params["type"])

            pc = RTCPeerConnection()
            pc_id = "PeerConnection(%s)" % uuid.uuid4()
            self.pcs.add(pc)

            def log_info(msg, *args):
                self.logger.info(pc_id + " " + msg, *args)

            log_info("Created for %s", request.remote)

            @pc.on("datachannel")
            def on_datachannel(channel):
                @channel.on("message")
                def on_message(message):
                    if isinstance(message, str) and message.startswith("ping"):
                        channel.send("pong" + message[4:])

            @pc.on("connectionstatechange")
            async def on_connectionstatechange():
                log_info("Connection state is %s", pc.connectionState)
                if pc.connectionState == "failed":
                    await pc.close()
                    self.pcs.discard(pc)

            @pc.on("track")
            def on_track(track):
                log_info("Track %s received", track.kind)

                @track.on("ended")
                async def on_ended():
                    log_info("Track %s ended", track.kind)

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

    async def on_shutdown(self, app):
        # close peer connections
        coros = [pc.close() for pc in self.pcs]
        await asyncio.gather(*coros)
        self.pcs.clear()

    async def start(self):
        logging.basicConfig(level=logging.INFO)

        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(
            "./certs/selfsigned.cert", "./certs/selfsigned.pem")

        app = web.Application()
        app.on_shutdown.append(self.on_shutdown)
        app.router.add_routes(self.routes)

        runner = web.AppRunner(app, handle_signals=True)
        await runner.setup()

        site = web.TCPSite(runner, self.host, self.port,
                           ssl_context=ssl_context)
        await site.start()

        print(f"Listening at https://{self.host}:{self.port}")

        while True:
            await asyncio.sleep(1)


def server_thread_runner():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    server = WebServer()

    loop.run_until_complete(server.start())
    loop.close()
