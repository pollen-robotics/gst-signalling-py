import argparse
import asyncio
import logging
import os

from gi.repository import Gst

from gst_signalling import GstSignallingConsumer
from gst_signalling.gst_abstract_role import GstSession
from gst_signalling.utils import find_producer_peer_id_by_name


def on_data_channel_message(data_channel, data: str) -> None:  # type: ignore[no-untyped-def]
    logging.info(f"Message from DataChannel: {data}")
    data_channel.send_string("pong")


def on_data_channel_callback(webrtc: Gst.Element, data_channel) -> None:  # type: ignore[no-untyped-def]
    data_channel.connect("on-message-string", on_data_channel_message)


def main(args: argparse.Namespace) -> None:
    peer_id = find_producer_peer_id_by_name(
        args.signaling_host, args.signaling_port, args.producer_name
    )

    close_evt = asyncio.Event()

    consumer = GstSignallingConsumer(
        host=args.signaling_host,
        port=args.signaling_port,
        producer_peer_id=peer_id,
    )

    @consumer.on("new_session")  # type: ignore[misc]
    def on_new_session(session: GstSession) -> None:
        pc = session.pc
        pc.connect("on-data-channel", on_data_channel_callback)

    @consumer.on("close_session")  # type: ignore[misc]
    def on_close_session(session: GstSession) -> None:
        close_evt.set()

    async def run_consumer(consumer: GstSignallingConsumer) -> None:
        await consumer.connect()
        await close_evt.wait()

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_consumer(consumer))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(consumer.close())


if __name__ == "__main__":
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
        os.environ["GST_DEBUG"] = "4"

    main(args)
