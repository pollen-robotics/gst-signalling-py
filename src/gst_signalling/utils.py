import argparse
import asyncio
from typing import Dict

from .gst_signalling import GstSignalling


async def get_list(host: str, port: int) -> Dict[str, Dict[str, str]]:
    producers = {}
    got_it = asyncio.Event()

    signalling = GstSignalling(host=host, port=port)
    await signalling.connect()

    @signalling.on("List")
    def on_list(found_producers: Dict[str, Dict[str, str]]) -> None:
        producers.update(found_producers)
        got_it.set()

    await signalling.send_list()
    await got_it.wait()

    await signalling.close()

    return producers


def get_producer_list(host: str, port: int) -> Dict[str, Dict[str, str]]:
    """Gets the list of producers from the signalling server.

    Args:
        host (str): Hostname of the signalling server.
        port (str): Port of the signalling server.
    Returns:
        Dict[str, Dict[str, str]]: Dictionary of producers, where the key is the producer ID
        and the value is a dictionary with the producer metadata (eg. name).
    """

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(get_list(host, port))


def find_producer_peer_id_by_name(host: str, port: int, name: str) -> str:
    """Finds the peer ID of a producer by its name.

    Args:
        name (str): Name of the producer.
    Returns:
        str: Producer peer ID (if multiple entries, the first is returned).
    Raises:
        KeyError: If the producer is not found.
    """
    producers = get_producer_list(host=host, port=port)

    for producer_id, producer_meta in producers.items():
        if producer_meta["name"] == name:
            return producer_id

    raise KeyError(f"Producer {name} not found.")


async def async_find_producer_peer_id_by_name(host: str, port: int, name: str) -> str:
    """Finds the peer ID of a producer by its name.

    Args:
        name (str): Name of the producer.
    Returns:
        str: Producer peer ID (if multiple entries, the first is returned).
    Raises:
        KeyError: If the producer is not found.
    """
    producers = await get_list(host=host, port=port)

    for producer_id, producer_meta in producers.items():
        if producer_meta["name"] == name:
            return producer_id

    raise KeyError(f"Producer {name} not found.")


def add_signaling_arguments(parser: argparse.ArgumentParser) -> None:
    """Adds command line arguments for GstSignaling.

    * signaling-host: Hostname of the signalling server.
    * signaling-port: Port of the signalling server.
    * role: Signalling role (consumer or producer).
    * name: Peer name.
    * remote-producer-peer-id: Producer peer_id (required in consumer role!).
    """
    parser.add_argument("--signaling-host", default="127.0.0.1", help="Gstreamer signaling host")
    parser.add_argument("--signaling-port", default=8443, help="Gstreamer signaling port")
    parser.add_argument("role", choices=["consumer", "producer"], help="Signaling role")
    parser.add_argument("--name", default="my-name", help="peer name")
    parser.add_argument(
        "--remote-producer-peer-id",
        type=str,
        help="producer peer_id (in consumer role, either set this or remote-producer-peer-name!)",
    )
    parser.add_argument(
        "--remote-producer-peer-name",
        type=str,
        default="remote-producer-peer-name",
        help="producer peer_name (in consumer role, either set this or remote-producer-peer-id!)",
    )
