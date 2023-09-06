import aiortc
from aiortc import RTCPeerConnection
import argparse
import asyncio
import logging
import time
from gst_signalling import GstSignallingProducer


def main(args: argparse.Namespace) -> None:
    async def setup_tracks(pc: RTCPeerConnection) -> None:
        channel = pc.createDataChannel("chat")

        async def send_pings() -> None:
            try:
                t0 = time.time()

                while True:
                    dt = time.time() - t0
                    channel.send(f"ping: {dt:.1f}s")
                    await asyncio.sleep(1)
            except aiortc.exceptions.InvalidStateError:
                print("Channel closed")

        @channel.on("open")  # type: ignore[misc]
        def on_open() -> None:
            asyncio.ensure_future(send_pings())

    producer = GstSignallingProducer(
        host=args.signaling_host,
        port=args.signaling_port,
        name=args.name,
        setup_tracks=setup_tracks,
    )

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(producer.serve4ever())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(producer.close())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--signaling-host", default="127.0.0.1", help="Gstreamer signaling host"
    )
    parser.add_argument(
        "--signaling-port", default=8443, help="Gstreamer signaling port"
    )
    parser.add_argument("--name", default="data-producer", help="Producer name")
    parser.add_argument("--verbose", "-v", action="count", default=0)
    args = parser.parse_args()

    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

    main(args)
