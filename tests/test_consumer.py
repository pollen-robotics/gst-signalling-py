import pytest

from gst_signalling import GstSignallingConsumer, GstSignallingProducer


# @pytest.mark.asyncio
async def test_consumer(signalling_host: str, signalling_port: int, producer_common: GstSignallingProducer) -> None:
    # close_evt = asyncio.Event()

    consumer = GstSignallingConsumer(
        host=signalling_host,
        port=signalling_port,
        producer_peer_id=producer_common.peer_id,
    )

    await consumer.connect()
    assert len(consumer.peer_id) == 36
    await consumer.close()
