import asyncio

import pytest
from gi.repository import Gst, GstWebRTC

from gst_signalling import GstSignallingConsumer, GstSignallingProducer
from gst_signalling.gst_abstract_role import GstSession

received_data_producer = ""
received_data_consumer = ""


async def test_data_exchange(signalling_host: str, signalling_port: int) -> None:
    reference_data_producer = "ping"
    reference_data_consumer = "pong"

    producer = GstSignallingProducer(
        host=signalling_host,
        port=signalling_port,
        name="producer",
    )

    @producer.on("new_session")  # type: ignore[misc]
    def on_new_session(session: GstSession) -> None:
        def on_open(channel: GstWebRTC.WebRTCDataChannel) -> None:
            channel.send_string(reference_data_producer)

        def on_data_channel_message(data_channel: GstWebRTC.WebRTCDataChannel, data: str) -> None:
            global received_data_producer
            received_data_producer = data

        pc = session.pc
        data_channel = pc.emit("create-data-channel", "chat", None)
        if data_channel:
            data_channel.connect("on-open", on_open)
            data_channel.connect("on-message-string", on_data_channel_message)

    await producer.connect()

    await asyncio.sleep(1)

    consumer = GstSignallingConsumer(
        host=signalling_host,
        port=signalling_port,
        producer_peer_id=producer.peer_id,
    )

    @consumer.on("new_session")  # type: ignore[misc]
    def on_new_session_consumer(session: GstSession) -> None:
        def on_data_channel_message(data_channel, data: str) -> None:  # type: ignore[no-untyped-def]
            global received_data_consumer
            received_data_consumer = data
            data_channel.send_string(reference_data_consumer)

        def on_data_channel_callback(webrtc: Gst.Element, data_channel) -> None:  # type: ignore[no-untyped-def]
            data_channel.connect("on-message-string", on_data_channel_message)

        pc = session.pc
        pc.connect("on-data-channel", on_data_channel_callback)

    await consumer.connect()

    await asyncio.sleep(1)

    await consumer.close()
    await producer.close()

    assert received_data_consumer == reference_data_producer
    assert received_data_producer == reference_data_consumer
