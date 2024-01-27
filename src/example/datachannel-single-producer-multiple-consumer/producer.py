import argparse
import asyncio
import logging
import os
import time

from gi.repository import Gst

from gst_signalling import GstSignallingProducer
from gst_signalling.gst_abstract_role import GstSession


def on_data_channel_message(data_channel, data) -> None:
    logging.info(f"Message from DataChannel: {data}")


def main(args: argparse.Namespace) -> None:
    producer = GstSignallingProducer(
        host=args.signaling_host,
        port=args.signaling_port,
        name=args.name,
    )

    FREQ_HZ = 1000

    @producer.on("new_session")  # type: ignore[misc]
    def on_new_session(session: GstSession) -> None:
        print("heeere")

        def on_open(channel: Gst.Element) -> None:
            asyncio.run_coroutine_threadsafe(send_pings(channel), loop)

        async def send_pings(channel: Gst.Element) -> None:
            try:
                t0 = time.time()

                while True:
                    dt = time.time() - t0
                    channel.send_string(f"ping: {dt:.1f}s")
                    await asyncio.sleep(1.0 / FREQ_HZ)
            except Exception as e:
                logging.error(f"{e}")

        pc = session.pc
        data_channel = pc.emit("create-data-channel", "chat", None)
        if data_channel:
            # self.on_data_channel(data_channel, pc)
            data_channel.connect("on-open", on_open)
            data_channel.connect("on-message-string", on_data_channel_message)
        else:
            logging.error("Failed to create data channel")

        """
        pc = session.pc

        channel = pc.createDataChannel("chat")

        @channel.on("message")  # type: ignore[misc]
        def on_message(message: str) -> None:
            print("received message:", message)

        async def send_pings() -> None:
            try:
                t0 = time.time()

                while True:
                    dt = time.time() - t0
                    channel.send(f"ping: {dt:.1f}s")
                    await asyncio.sleep(1.0 / freq_hz)
            except aiortc.exceptions.InvalidStateError:
                print("Channel closed")

        @channel.on("open")  # type: ignore[misc]
        def on_open() -> None:
            asyncio.ensure_future(send_pings())
        """

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
        os.environ["GST_DEBUG"] = "4"

    main(args)
