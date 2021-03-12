"""Establish a video stream using WebRTC."""
import asyncio
import json

from aiortc import RTCPeerConnection
from aiortc.mediastreams import MediaStreamTrack
from aiortc.rtcdatachannel import RTCDataChannel
from aiortc.rtcsessiondescription import RTCSessionDescription
from pyee import AsyncIOEventEmitter

from mimic.Utils.Time import latency, timestamp


class WebRTCVideoStream():
    """
    Establish a video stream using WebRTC.

    The following events are emitted and can be listened to using the `events` property:
    - "metadata" (metadata: VideoStreamMetadata): When video metadata is received
    - "ping" (latency: int): The current latency of the connection in milliseconds
    - "newtrack" (track: MediaStreamTrack): When a new video track is registered to the RTC connection
    - "closed": When the video stream ends or the RTC connection is closed

    >>> video_stream = WebRTCVideoStream(sdp, type)
    >>>
    >>> @video_stream.events.on("newtrack")
    >>> def on_newtrack(track: MediaStreamTrack):
    >>>     print("Got track")
    """

    sdp: str
    type: str

    peer_connection: RTCPeerConnection
    events = AsyncIOEventEmitter()

    def __init__(self, sdp: str, type: str):
        """
        Instance of `WebRTCVideoStream`.

        Call `acknowledge` to establish connection.

        Args:
            sdp (str): Session description protocol sent in an offer from client
            type (str): Media type sent in an offer from client
        """
        self.sdp = sdp
        self.type = type

    async def acknowledge(self) -> str:
        """
        Generate answer to WebRTC offer and establish events.

        Returns:
            str: Stringified JSON object of WebRTC answer
        """
        offer = RTCSessionDescription(
            sdp=self.sdp, type=self.type)

        self.peer_connection = RTCPeerConnection()

        @self.peer_connection.on("datachannel")
        def on_datachannel(channel: RTCDataChannel):
            @channel.on("message")
            async def on_message(message):
                if isinstance(message, str):
                    if channel.label == "metadata":
                        # Parse video stream metadata into structured class
                        metadata_json = json.loads(message)
                        self.events.emit("metadata", VideoStreamMetadata(
                            metadata_json['width'], metadata_json['height'], metadata_json['framerate']))

                    elif channel.label == "latency":
                        message_timestamp = int(message)

                        # If the client sends a -1, then it is the initial
                        # connection and should be ignored
                        if message_timestamp != -1:
                            self.events.emit(
                                "ping", latency(message_timestamp))

                        # Wait before sending another ping so we aren't spamming
                        # the connection
                        await asyncio.sleep(1)
                        channel.send(str(timestamp()))

        @self.peer_connection.on("connectionstatechange")
        async def on_connectionstatechange():
            if self.peer_connection.connectionState == "failed":
                await self.peer_connection.close()
                self.events.emit("closed")

        @self.peer_connection.on("track")
        def on_track(track: MediaStreamTrack):
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


class VideoStreamMetadata():
    """Video stream resolution and framerate."""

    def __init__(self, width: int, height: int, framerate: int):
        """
        Structure metadata about video stream.

        Args:
            width (int): Video stream width in pixels
            height (int): Video stream height in pixels
            framerate (int): Video stream framerate in frames per second
        """
        self.width = width
        self.height = height
        self.framerate = framerate
