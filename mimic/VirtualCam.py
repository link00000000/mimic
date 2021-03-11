from aiortc import MediaStreamTrack
from av import VideoFrame


class VirtualCam:
    kind = "video"

    track: MediaStreamTrack

    def __init__(self, track: MediaStreamTrack):
        super().__init__()
        self.track = track

    async def recv(self) -> VideoFrame:
        frame = await self.track.recv()

        # @TODO Paint `VideoFrame`s to pyvirtualcam

        return frame
