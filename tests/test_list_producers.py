import pytest

from gst_signalling import GstSignallingProducer, utils


def test_empty_list(signalling_host: str, signalling_port: int) -> None:
    producers = utils.get_producer_list(signalling_host, signalling_port)

    assert len(producers) == 0


@pytest.mark.asyncio
async def test_one_producer(signalling_host: str, signalling_port: int, producer_common: GstSignallingProducer) -> None:
    producers = await utils.get_list(signalling_host, signalling_port)

    assert len(producers) == 1
    assert list(producers.items())[0][1]["name"] == "producer_common"
