import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import pyee
from websockets.legacy.client import connect, WebSocketClientProtocol


class GstSignalling(pyee.AsyncIOEventEmitter):
    def __init__(self, host: str, port: int) -> None:
        pyee.AsyncIOEventEmitter.__init__(self)  # type: ignore[no-untyped-call]

        self.logger = logging.getLogger(__name__)

        self.ws: Optional[WebSocketClientProtocol] = None
        self.host = host
        self.port = port

        self.peer_id: Optional[str] = None
        self.session_id: Optional[str] = None

    async def connect(self) -> None:
        if self.ws is not None:
            raise RuntimeError("Already connected.")

        url = f"ws://{self.host}:{self.port}"
        self.logger.info(f"Connecting to {url}")
        self.ws = await connect(url)
        self.logger.info("Connected.")

        asyncio.create_task(self._handler())

    async def close(self) -> None:
        if self.ws is None:
            raise RuntimeError("Not connected.")

        self.logger.info("Closing connection.")
        await self.ws.close()
        self.logger.info("Closed.")

    # Input messages handler
    async def _handler(self) -> None:
        assert self.ws is not None

        self.logger.info("Starting input message handler.")

        async for data in self.ws:
            assert isinstance(data, str)

            self.logger.info(f"Received message: {data}")
            message: Dict[str, Any] = json.loads(data)

            # Welcoming message, sets the Peer ID linked to a new connection
            if message["type"] == "welcome":
                peer_id = message["peerId"]
                self.peer_id = peer_id
                self.emit("Welcome", peer_id)

            # Notifies listener that a peer status has changed
            elif message["type"] == "peerStatusChanged":
                self.logger.error(f"Unimplemented message handler {message}")

            # Instructs a peer to generate an offer and inform about the session ID
            elif message["type"] == "startSession":
                peer_id = message["peerId"]
                session_id = message["sessionId"]
                self.session_id = session_id
                self.emit("StartSession", peer_id, session_id)

            # Let consumer know that the requested session is starting with the specified identifier
            elif message["type"] == "sessionStarted":
                peer_id = message["peerId"]
                session_id = message["sessionId"]
                self.session_id = session_id
                self.emit("SessionStarted", peer_id, session_id)

            # Signals that the session the peer was in was ended
            elif message["type"] == "endSession":
                self.session_id = None
                self.emit("EndSession", session_id)

            # Messages directly forwarded from one peer to another
            elif message["type"] == "peer":
                assert message["sessionId"] == self.session_id
                message = dict(message)
                del message["type"]
                del message["sessionId"]
                self.emit("Peer", message)

            # Provides the current list of consumer peers
            elif message["type"] == "list":
                self.logger.error(f"Unimplemented message handler {message}")

            elif message["type"] == "error":
                details = message["details"]
                self.logger.error(f'An error occured: "{details}"')
                self.emit("Error", details)

            else:
                self.logger.warning(f"Received unknown message type: {message}.")

    # Output messages publisher
    async def set_peer_status(self, roles: List[str], name: str) -> None:
        if self.ws is None:
            raise RuntimeError("Not connected.")
        if self.peer_id is None:
            raise RuntimeError("PeerId not yet received.")

        for role in roles:
            if role not in ("consumer", "listener", "producer"):
                raise ValueError(f"Invalid role {role}.")

        message = {
            "type": "setPeerStatus",
            "roles": roles,
            "meta": {"name": name},
            "peerId": self.peer_id,
        }

        await self.send(message)

    async def start_session(self, peer_id: str) -> None:
        message = {"type": "startSession", "peerId": peer_id}
        await self.send(message)

    async def send_peer_message(self, type: str, peer_message: str) -> None:
        message = {
            "type": "peer",
            "sessionId": self.session_id,
            type: peer_message,
        }

        await self.send(message)

    async def send(self, message: Dict[str, Any]) -> None:
        if self.ws is None:
            raise RuntimeError("Not connected.")

        self.logger.debug(f"Sending message: {message}")
        await self.ws.send(json.dumps(message))
