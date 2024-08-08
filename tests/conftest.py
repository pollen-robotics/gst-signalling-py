import pytest


@pytest.fixture(scope="package")
def signalling_host() -> str:
    return "127.0.0.1"


@pytest.fixture(scope="package")
def signalling_port() -> int:
    return 8443
