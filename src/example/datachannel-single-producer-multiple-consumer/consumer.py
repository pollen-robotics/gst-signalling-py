import asyncio
import logging
from gst_signalling import GstSignallingConsumer
from gst_signalling.utils import find_producer_peer_id_by_name


async def run_consumer(consumer: GstSignallingConsumer) -> None:
    await consumer.connect()

    while True:
        await asyncio.sleep(1)


async def setup_tracks(pc):
    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            print("received message:", message)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--signaling-host", default="127.0.0.1", help="Gstreamer signaling host"
    )
    parser.add_argument(
        "--signaling-port", default=8443, help="Gstreamer signaling port"
    )
    parser.add_argument(
        "--producer-name", default="data-producer", help="Producer name"
    )
    parser.add_argument("--verbose", "-v", action="count", default=0)
    args = parser.parse_args()

    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

    peer_id = find_producer_peer_id_by_name(
        args.signaling_host, args.signaling_port, args.producer_name
    )
    consumer = GstSignallingConsumer(
        host=args.signaling_host,
        port=args.signaling_port,
        producer_peer_id=peer_id,
        setup_pc_tracks=setup_tracks,
    )

    coro = run_consumer(consumer)

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(coro)
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(consumer.close())
