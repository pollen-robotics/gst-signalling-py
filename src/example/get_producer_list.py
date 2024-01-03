import argparse
import logging

from gst_signalling import utils


def get_producer_list(args: argparse.Namespace) -> None:
    """Main function."""
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    producers = utils.get_producer_list(args.signalling_host, args.signalling_port)

    if producers:
        print("List received, producers:")
        for producer_id, producer_meta in producers.items():
            print(f"  - {producer_id}: {producer_meta}")
    else:
        print("List received, no producers.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Get gstreamer producer list")
    parser.add_argument("--signalling-host", default="127.0.0.1")
    parser.add_argument("--signalling-port", default=8443, type=int)
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    get_producer_list(args)


if __name__ == "__main__":
    main()
