import pytest

from gst_signalling import GstSignallingProducer


# @pytest.mark.asyncio
async def test_simple_producer(signalling_host: str, signalling_port: int) -> None:
    producer = GstSignallingProducer(
        host=signalling_host,
        port=signalling_port,
        name="pytest producer",
    )

    await producer.connect()
    assert len(producer.peer_id) == 36
    await producer.close()
