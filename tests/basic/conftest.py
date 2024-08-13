import pytest

from gst_signalling import GstSignallingProducer


@pytest.fixture(scope="package")
async def producer_common(signalling_host: str, signalling_port: int) -> GstSignallingProducer:
    """
    Same producer for all tests
    """

    producer = GstSignallingProducer(
        host=signalling_host,
        port=signalling_port,
        name="producer_common",
    )

    await producer.connect()

    yield producer

    await producer.close()
