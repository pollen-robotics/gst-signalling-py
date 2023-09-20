import argparse
import os
import time
import logging
from gst_signalling import utils
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

def get_producer_id(host : str, port : int, producer_name : str) -> str:
    #Todo: add a timeout
    while True:
        # ToDo: create a client at each iteration. May be not optimal
        producers = utils.get_producer_list(host=host, port=port)

        if producers:
            logging.info("List received, producers:")
            for producer_id, producer_meta in producers.items():
                logging.info(f"  - {producer_id}: {producer_meta}")
                if producer_meta['name'] == producer_name:
                    logging.info("Target producer found.")
                    return producer_id
            logging.warning("Target producer not found.")
        else:
            logging.info("List received, no producers.")
        
        time.sleep(1)


def start_consumer(host : str, port : int, producer_id : str) -> None:
    Gst.init(None)

    cmd = f"playbin uri=gstwebrtc://{host}:{port}?peer-id={producer_id}"

    logging.info(cmd)

    pipeline = Gst.parse_launch(cmd)

    pipeline.set_state(Gst.State.PLAYING)

    try:
        while True:        
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("User exit")
    finally:
        pipeline.set_state(Gst.State.NULL)

def main() -> None:
    parser = argparse.ArgumentParser(description="Get gstreamer producer list")
    parser.add_argument("--signalling-host", default="127.0.0.1")
    parser.add_argument("--signalling-port", default=8443, type=int)
    parser.add_argument("--producer-name", type=str, required=True)
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        os.environ["GST_DEBUG"] = "2"

    id = get_producer_id(args.signalling_host, args.signalling_port, args.producer_name)

    logging.info(id)

    start_consumer(args.signalling_host, args.signalling_port, id)


if __name__ == "__main__":
    main()
