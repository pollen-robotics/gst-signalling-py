import pytest

from gst_signalling import utils


def test_empty_list(signalling_host: str, signalling_port: int) -> None:
    producers = utils.get_producer_list(signalling_host, signalling_port)

    assert len(producers) == 0
