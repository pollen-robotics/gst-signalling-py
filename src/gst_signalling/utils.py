import asyncio
from typing import Dict

from .gst_signalling import GstSignalling


async def get_producer_list(signalling: GstSignalling) -> Dict[str, Dict[str, str]]:
    """Gets the list of producers from the signalling server.

    Args:
        signalling (GstSignalling): GstSignalling instance (it should already be connected).
    Returns:
        Dict[str, Dict[str, str]]: Dictionary of producers, where the key is the producer ID
        and the value is a dictionary with the producer metadata (eg. name).
    """
    producers = {}
    got_it = asyncio.Event()

    @signalling.on("List")
    def on_list(found_producers: Dict[str, Dict[str, str]]) -> None:
        producers.update(found_producers)
        got_it.set()

    await signalling.send_list()
    await got_it.wait()

    signalling.remove_listener("List", on_list)

    return producers
