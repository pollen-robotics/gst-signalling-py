import argparse
import asyncio
import logging
from typing import Dict, List

from gst_signalling import GstSignallingListener


def main(args: argparse.Namespace) -> None:
    listener = GstSignallingListener(
        host=args.signaling_host,
        port=args.signaling_port,
        name=args.name,
    )

    @listener.on("PeerStatusChanged")  # type: ignore[misc]
    def on_peer_status_changed(
        peer_id: str,
        roles: List[str],
        meta: Dict[str, str],
    ) -> None:
        print(f'Peer "{peer_id}" changed roles to {roles} with meta {meta}')

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(listener.serve4ever())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(listener.close())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--signaling-host", default="127.0.0.1", help="Gstreamer signaling host")
    parser.add_argument("--signaling-port", default=8443, help="Gstreamer signaling port")
    parser.add_argument("--name", default="listener", help="Producer name")
    parser.add_argument("--verbose", "-v", action="count", default=0)
    args = parser.parse_args()

    if args.verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

    main(args)
