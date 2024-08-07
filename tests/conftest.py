import pytest


@pytest.fixture
def signalling_host() -> str:
    return "127.0.0.1"


@pytest.fixture
def signalling_port() -> int:
    return 8443
