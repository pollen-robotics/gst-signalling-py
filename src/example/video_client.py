import argparse
import asyncio
import logging

from aiortc.contrib.media import MediaBlackhole
from audiotrack import AudioTrack
from videotrack import VideoTrack

from gst_signalling.gst_abstract_role import GstSession
from gst_signalling.gst_consumer import GstSignallingConsumer
from gst_signalling.utils import find_producer_peer_id_by_name


class VideoClient:
    def __init__(self, signalling_url: str, signalling_port: int, peer_id: str):
        self.logger = logging.getLogger(__name__)
        self.client = GstSignallingConsumer(signalling_url, signalling_port, peer_id)
        self.media = MediaBlackhole()
        self.audio_track = None
        self.video_track = None

        @self.client.on("new_session")  # type: ignore[misc]
        def on_new_session(session: GstSession) -> None:
            pc = session.pc

            @pc.on("track")
            async def on_track(track):
                self.logger.info("Receiving %s" % track.kind)
                if track.kind == "audio":
                    if self.audio_track is not None:
                        self.logger.warning("Already have an audio track, ignoring")
                        return
                    self.audio_track = AudioTrack(track)
                    self.media.addTrack(self.audio_track)
                    await self.media.start()
                elif track.kind == "video":
                    if self.video_track is not None:
                        self.logger.warning("Already have a video track, ignoring")
                        return
                    self.video_track = VideoTrack(track)
                    self.media.addTrack(self.video_track)
                    await self.media.start()

    async def start(self) -> None:
        await self.client.connect()

    async def serve4ever(self) -> None:
        await self.client.consume()


async def run_client(signalling_host: str, signalling_port: int, peer_id: str) -> None:
    client = VideoClient(signalling_host, signalling_port, peer_id)
    await client.start()
    await client.serve4ever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Video client example")
    parser.add_argument("--signalling-host", default="127.0.0.1")
    parser.add_argument("--signalling-port", default=8443, type=int)
    parser.add_argument("--verbose", "-v", action="count")
    parser.add_argument("--name", help="Producer name to search for", required=True)
    args = parser.parse_args()

    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

    try:
        peer_id = find_producer_peer_id_by_name(
            args.signalling_host, args.signalling_port, args.name
        )
    except Exception as e:
        logging.error(f"Error finding producer peer ID: {e}")
        return
    print(f"Found producer peer ID: {peer_id}")

    asyncio.run(run_client(args.signalling_host, args.signalling_port, peer_id))


if __name__ == "__main__":
    main()
