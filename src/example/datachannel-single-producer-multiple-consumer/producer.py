from aiortc import RTCPeerConnection
import asyncio
import logging
import time
from gst_signalling import GstSignallingProducer


async def run_producer(producer: GstSignallingProducer) -> None:
    await producer.connect()

    while True:
        await asyncio.sleep(1)


async def setup_tracks(pc: RTCPeerConnection) -> None:
    channel = pc.createDataChannel("chat")

    async def send_pings() -> None:
        while True:
            channel.send("ping %d" % current_stamp())
            await asyncio.sleep(1)

    @channel.on("open")
    def on_open() -> None:
        asyncio.ensure_future(send_pings())


time_start = None


def current_stamp() -> int:
    global time_start

    if time_start is None:
        time_start = time.time()
        return 0
    else:
        return int((time.time() - time_start) * 1000000)


if __name__ == "__main__":
    import argparse

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

    producer = GstSignallingProducer(
        host=args.signaling_host,
        port=args.signaling_port,
        name=args.name,
        setup_tracks=setup_tracks,
    )

    coro = run_producer(producer)

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(coro)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(producer.close())
