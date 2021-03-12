import json

from aiortc import RTCPeerConnection
from aiortc.rtcsessiondescription import RTCSessionDescription
from pyee import AsyncIOEventEmitter


class WebRTCVideoStream():
    sdp: str
    type: str

    peer_connection: RTCPeerConnection
    events = AsyncIOEventEmitter()

    def __init__(self, sdp: str, type: str):
        self.sdp = sdp
        self.type = type

    async def acknowledge(self):
        offer = RTCSessionDescription(
            sdp=self.sdp, type=self.type)

        self.peer_connection = RTCPeerConnection()

        @self.peer_connection.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(message):
                if isinstance(message, str) and message.startswith("ping"):
                    self.events.emit("datachannelmessage", message)

                    channel.send("pong" + message[4:])

        @self.peer_connection.on("connectionstatechange")
        async def on_connectionstatechange():
            if self.peer_connection.connectionState == "failed":
                await self.peer_connection.close()
                self.events.emit("closed")

        @self.peer_connection.on("track")
        def on_track(track):
            if track.kind != 'video':
                return

            self.events.emit("newtrack", track)

            @track.on("ended")
            async def on_ended():
                self.events.emit("closed")

        # handle offer
        await self.peer_connection.setRemoteDescription(offer)

        # send answer
        answer = await self.peer_connection.createAnswer()
        await self.peer_connection.setLocalDescription(answer)

        return json.dumps(
            {"sdp": self.peer_connection.localDescription.sdp,
             "type": self.peer_connection.localDescription.type}
        )
