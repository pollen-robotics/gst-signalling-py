from aiortc import RTCIceCandidate, RTCSessionDescription
from aiortc.contrib.signaling import object_from_string, object_to_string
from aiortc.sdp import candidate_from_sdp
import argparse
import asyncio
import json
import logging
from typing import Any, Optional, Union

from .gst_signalling import GstSignalling
from .utils import find_producer_peer_id_by_name


class GstSignalingForAiortc:
    """Gstreamer signalling for aiortc.

    This class is a wrapper around GstSignalling that provides a simple interface,
    that should be mostly compatible with aiortc examples.
    """

    def __init__(
        self,
        signaling_host: str,
        signaling_port: int,
        role: str,
        name: str,
        remote_producer_peer_id: Optional[str] = None,
    ):
        """Initializes the signalling peer.

        Args:
            signaling_host (str): Hostname of the signalling server.
            signaling_port (int): Port of the signalling server.
            role (str): Signalling role (consumer or producer).
            name (str): Peer name.
            remote_producer_peer_id (Optional[str], optional): Producer peer_id (required in consumer role!).
        """
        self.logger = logging.getLogger(__name__)
        self.signalling = GstSignalling(signaling_host, signaling_port)

        if role not in ("consumer", "producer"):
            raise ValueError("invalid role {role}")
        self.role = role

        self.name = name

        self.peer_id: Optional[str] = None
        self.peer_id_evt = asyncio.Event()

        self.session_id: Optional[str] = None
        self.session_id_evt = asyncio.Event()

        self.peer_msg_queue: asyncio.Queue[
            Union[RTCSessionDescription, RTCIceCandidate, object]
        ] = asyncio.Queue()

        self._setup(remote_producer_peer_id)

    def _setup(self, remote_producer_peer_id: Optional[str] = None) -> None:
        @self.signalling.on("Welcome")
        def on_welcome(peer_id: str) -> None:
            self.logger.info(f"Welcome received, peer_id: {peer_id}")
            self.peer_id = peer_id
            self.peer_id_evt.set()

        if self.role == "producer":
            self._setup_producer()
        elif self.role == "consumer":
            if remote_producer_peer_id is None:
                raise ValueError(
                    "In consumer role, you have to specify the remote-producer-peer-id!"
                )
            self._setup_consumer(remote_producer_peer_id)

        @self.signalling.on("Peer")
        async def on_peer(session_id: str, message: dict[str, Any]) -> None:
            assert self.session_id == session_id
            obj = self._parse_peer_message(message)
            if obj is not None:
                await self.peer_msg_queue.put(obj)

        @self.signalling.on("EndSession")
        async def on_end_session(session_id: str) -> None:
            await self.peer_msg_queue.put(BYE)

        @self.signalling.on("Error")
        async def on_error(details: str) -> None:
            self.logger.error(f'Connection closed with error: "{details}"')
            await self.peer_msg_queue.put(BYE)

    def _parse_peer_message(
        self, message: dict[str, Any]
    ) -> Optional[Union[RTCSessionDescription, RTCIceCandidate]]:
        if "sdp" in message:
            message = message["sdp"]
        elif "ice" in message:
            message = message["ice"]
        else:
            raise ValueError(f"Invalid message {message}")

        if "type" in message:
            obj = object_from_string(json.dumps(message))
            return obj
        elif "candidate" in message:
            if message["candidate"] == "":
                self.logger.info("Received empty candidate, ignoring")
                return None

            obj = candidate_from_sdp(message["candidate"].split(":", 1)[1])
            obj.sdpMLineIndex = message["sdpMLineIndex"]
            return obj
        else:
            self.logger.error(f"Failed to parse message: {message}")
            return None

    def _setup_producer(self) -> None:
        @self.signalling.on("StartSession")
        def on_start_session(peer_id: str, session_id: str) -> None:
            self.logger.info(
                f"StartSession received, peer_id: {peer_id}, session_id: {session_id}"
            )
            self.session_id = session_id
            self.session_id_evt.set()

    def _setup_consumer(self, remote_producer_peer_id: str) -> None:
        self.remote_producer_peer_id = remote_producer_peer_id

        @self.signalling.on("SessionStarted")
        def on_session_started(peer_id: str, session_id: str) -> None:
            self.logger.info(
                f"SessionStarted received, peer_id: {peer_id}, session_id: {session_id}"
            )
            self.session_id = session_id
            self.session_id_evt.set()

    async def connect(self) -> None:
        """Connects to the signalling server.

        This method will block until the connection is established (meaning we received a PeerID and a SessionID).
        This method has to be called before any other method.
        """
        await self.signalling.connect()
        await self.peer_id_evt.wait()

        if self.role == "producer":
            await self.signalling.set_peer_status(roles=["producer"], name=self.name)

        elif self.role == "consumer":
            await self.signalling.start_session(peer_id=self.remote_producer_peer_id)

        await self.session_id_evt.wait()

        self.logger.info(
            f"Connected, peer_id: {self.peer_id}, session_id: {self.session_id}"
        )

    async def close(self) -> None:
        """Closes the connection to the signalling server."""
        await self.signalling.close()

    async def send(
        self, message: Union[RTCIceCandidate, RTCSessionDescription]
    ) -> None:
        """Sends a message to the other peer (SDP or ICECandidate).

        Args:
            message (Union[RTCIceCandidate, RTCSessionDescription]): Message to send.
        """
        data = json.loads(object_to_string(message))
        assert self.session_id is not None

        if isinstance(message, RTCSessionDescription):
            await self.signalling.send_peer_message(self.session_id, "sdp", data)
        elif isinstance(message, RTCIceCandidate):
            await self.signalling.send_peer_message(self.session_id, "ice", data)
        else:
            raise ValueError(f"Invalid message type {type(message)}")

    async def receive(self) -> Union[RTCIceCandidate, RTCSessionDescription]:
        """Receives a message from the other peer (SDP or ICECandidate)."""
        obj = await self.peer_msg_queue.get()
        self.logger.info(f"Received peer message: {obj}")
        return obj


BYE = object()


def create_signaling(args: argparse.Namespace) -> GstSignalingForAiortc:
    """Creates a GstSignalingForAiortc instance from command line arguments."""
    if args.role == "consumer":
        if (
            args.remote_producer_peer_id is None
            and args.remote_producer_peer_name is None
        ):
            raise ValueError(
                "In consumer role, you have to specify the remote-producer-peer-id or remote-producer-peer-name!"
            )
        elif args.remote_producer_peer_id is not None:
            remote_producer_peer_id = args.remote_producer_peer_id
        else:
            remote_producer_peer_id = find_producer_peer_id_by_name(
                host=args.signaling_host,
                port=args.signaling_port,
                name=args.remote_producer_peer_name,
            )
    else:
        remote_producer_peer_id = None

    return GstSignalingForAiortc(
        signaling_host=args.signaling_host,
        signaling_port=args.signaling_port,
        role=args.role,
        name=args.name,
        remote_producer_peer_id=remote_producer_peer_id,
    )


def add_signaling_arguments(parser: argparse.ArgumentParser) -> None:
    """Adds command line arguments for GstSignalingForAiortc.

    * signaling-host: Hostname of the signalling server.
    * signaling-port: Port of the signalling server.
    * role: Signalling role (consumer or producer).
    * name: Peer name.
    * remote-producer-peer-id: Producer peer_id (required in consumer role!).
    """
    parser.add_argument(
        "--signaling-host", default="127.0.0.1", help="Gstreamer signaling host"
    )
    parser.add_argument(
        "--signaling-port", default=8443, help="Gstreamer signaling port"
    )
    parser.add_argument("role", choices=["consumer", "producer"], help="Signaling role")
    parser.add_argument("--name", default="aiortc-peer", help="peer name")
    parser.add_argument(
        "--remote-producer-peer-id",
        type=str,
        help="producer peer_id (in consumer role, either set this or remote-producer-peer-name!)",
    )
    parser.add_argument(
        "--remote-producer-peer-name",
        type=str,
        default="aiortc-peer",
        help="producer peer_name (in consumer role, either set this or remote-producer-peer-id!)",
    )
