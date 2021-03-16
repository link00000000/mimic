import asyncio
import json
import logging
import os
import ssl
import uuid
from multiprocessing.connection import Connection
from threading import Event

from aiohttp import web
from aiohttp.web_request import Request
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription

from mimic.Pipeable import LogMessage
from mimic.Utils.Host import resolve_host

ROOT = os.path.abspath('mimic/public')


class WebServer:
    logger = logging.getLogger("pc")
    pcs: set[RTCPeerConnection] = set()
    routes = web.RouteTableDef()

    def __init__(self, host=resolve_host(), port=8080, pipe: Connection = None, stop_event=Event()) -> None:
        self.__host = host
        self.__port = port
        self.__pipe = pipe
        self.__stop_event = stop_event

        @self.routes.get('/')
        async def index(request):
            content = open(os.path.join(ROOT, "index.html"), "r").read()
            self.__pipe.send(LogMessage("Got a request on '/'"))
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
            request_body = await request.json()

            if request_body['sdp'] is None or request_body['type'] is None:
                return web.Response(status=400, text="Bad request, must include 'sdp' and 'type'.")

            offer = RTCSessionDescription(
                sdp=request_body["sdp"], type=request_body["type"])

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

    async def __on_shutdown(self):
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
        app.router.add_routes(self.routes)

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


def server_thread_runner(pipe: Connection, stop_event: Event):
    """Initialize and run the web server on a worker thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    server = WebServer(pipe=pipe, stop_event=stop_event)

    loop.run_until_complete(server.start())
