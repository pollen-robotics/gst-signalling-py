import argparse
from gst_signalling import GstSignalling


async def main(args: argparse.Namespace) -> None:
    """Main function."""
    signalling = GstSignalling(host="localhost", port=8443)

    @signalling.on("Welcome")
    def on_welcome(peer_id: str) -> None:
        print(f"Welcome received, peer_id: {peer_id}")

    await signalling.connect()
    await signalling.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get producer list")
    parser.add_argument("--signalling-host", default="127.0.0.1")
    parser.add_argument("--signalling-port", default=8443, type=int)
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    main(args)
