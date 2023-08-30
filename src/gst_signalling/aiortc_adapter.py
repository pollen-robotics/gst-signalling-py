from aiortc import RTCIceCandidate, RTCSessionDescription
from aiortc.contrib.signaling import object_from_string, object_to_string
import argparse
import asyncio
import json
import logging
from typing import Any, Optional, Union

from .gst_signalling import GstSignalling


class GstSignalingForAiortc:
    def __init__(
        self,
        signaling_host: str,
        signaling_port: int,
        role: str,
        name: str,
        remote_producer_peer_id: Optional[str] = None,
    ):
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
        async def on_peer(message: dict[str, Any]) -> None:
            if "sdp" in message:
                message = message["sdp"]
            elif "ice" in message:
                message = message["ice"]
            else:
                raise ValueError(f"Invalid message {message}")

            obj = object_from_string(json.dumps(message))
            await self.peer_msg_queue.put(obj)

        @self.signalling.on("EndSession")
        async def on_end_session(session_id: str) -> None:
            await self.peer_msg_queue.put(BYE)

        @self.signalling.on("Error")
        async def on_error(details: str) -> None:
            self.logger.error(f'Connection closed with error: "{details}"')
            await self.peer_msg_queue.put(BYE)

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
        await self.signalling.close()

    async def send(
        self, message: Union[RTCIceCandidate, RTCSessionDescription]
    ) -> None:
        if isinstance(message, RTCSessionDescription):
            await self.signalling.send_peer_message(
                "sdp", json.loads(object_to_string(message))
            )
        elif isinstance(message, RTCIceCandidate):
            await self.signalling.send_peer_message(
                "ice", json.loads(object_to_string(message))
            )
        else:
            raise ValueError(f"Invalid message type {type(message)}")

    async def receive(self) -> Union[RTCIceCandidate, RTCSessionDescription]:
        obj = await self.peer_msg_queue.get()
        self.logger.info(f"Received peer message: {obj}")
        return obj


BYE = object()


def create_signaling(args: argparse.Namespace) -> GstSignalingForAiortc:
    return GstSignalingForAiortc(
        signaling_host=args.signaling_host,
        signaling_port=args.signaling_port,
        role=args.role,
        name=args.name,
        remote_producer_peer_id=args.remote_producer_peer_id,
    )


def add_signaling_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--signaling-host", default="127.0.0.1", help="Gstreamer signaling host"
    )
    parser.add_argument(
        "--signaling-port", default=8443, help="Gstreamer signaling port"
    )
    parser.add_argument("role", choices=["consumer", "producer"], help="Signaling role")
    parser.add_argument("--name", default="python-peer", help="peer name")
    parser.add_argument(
        "--remote-producer-peer-id",
        type=str,
        help="producer peer_id (required in consumer role!)",
    )
