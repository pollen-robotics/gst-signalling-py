import pytest

from gst_signalling import utils


def test_empty_list(signalling_host: str, signalling_port: int) -> None:
    producers = utils.get_producer_list(signalling_host, signalling_port)

    assert len(producers) == 0


# @pytest.mark.asyncio
# async def test_some_asyncio_code(signalling_host: str, signalling_port: int) -> None:
