import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from pyee.asyncio import AsyncIOEventEmitter
from websockets.legacy.client import WebSocketClientProtocol, connect


class GstSignalling(AsyncIOEventEmitter):
    """Signalling peer for the GStreamer WebRTC implementation.

    This class is used to communicate with a GStreamer WebRTC signalling server.
    It relies on an async websocket client to communicate with the server.

    It can be used for the consumer, producer and listener roles. All following messages are supported:

    Peer --> Server
    - "SetPeerStatus": Set current peer status (see set_peer_status)
    - "StartSession":  Start a session with a producer peer (see start_session)
    - "EndSession": End an existing session (see end_session)
    - "Peer": Send a message to a peer the sender is currently in session with (see send_peer_message)
    - "List": Retrieve the current list of producers (see get_list)

    Server --> Peer
    - "Welcome": Welcoming message, sets the Peer ID linked to a new connection
    - "PeerStatusChanged": Notifies listeners that a peer status has changed
    - "StartSession": Instructs a peer to generate an offer and inform about the session ID
    - "SessionStarted": Let consumer know that the requested session is starting with the specified identifier
    - "EndSession": Signals that the session the peer was in was ended
    - "Peer": Messages directly forwarded from one peer to another
    - "List": Provides the current list of consumer peers
    - "Error": Notifies that an error occured with the peer's current session

    Each receive message can be listened to by registering a callback with the corresponding event name.
    For instance, to listen to the "Welcome" message, you can do:

    signalling = GstSignalling(host="localhost", port=8443)

    @signalling.on("Welcome")
    def on_welcome(peer_id: str) -> None:
        print(f"Welcome received, peer_id: {peer_id}")
    """

    def __init__(self, host: str, port: int) -> None:
        """Initializes the signalling peer.

        Args:
            host (str): Hostname of the signalling server.
            port (int): Port of the signalling server."""
        AsyncIOEventEmitter.__init__(self)

        self.logger = logging.getLogger(__name__)

        self.ws: Optional[WebSocketClientProtocol] = None
        self.host = host
        self.port = port

        self.peer_id: Optional[str] = None
        self.handler_task: Optional[asyncio.Task[None]] = None

    async def connect(self) -> None:
        """Connects to the signalling server."""
        if self.ws is not None:
            raise RuntimeError("Already connected.")

        url = f"ws://{self.host}:{self.port}"
        self.logger.info(f"Connecting to {url}")
        self.ws = await connect(url, ping_interval=None)
        self.logger.info("Connected.")

        self.handler_task = asyncio.create_task(self._handler())

    async def close(self) -> None:
        """Closes the connection to the signalling server."""
        if self.ws is None:
            raise RuntimeError("Not connected.")

        if self.handler_task is not None:
            self.handler_task.cancel()
            await self.handler_task
            self.handler_task = None

        self.logger.info("Closing connection.")
        await self.ws.close()
        self.logger.debug("Closed.")

    # Messages (server --> peer)
    async def _handler(self) -> None:
        assert self.ws is not None

        self.logger.info("Starting input message handler.")

        try:
            async for data in self.ws:
                assert isinstance(data, str)

                self.logger.debug(f"Received message: {data}")
                message: Dict[str, Any] = json.loads(data)
                await self._handle_messages(message)
        except asyncio.CancelledError:
            self.logger.info("Input message handler cancelled.")

    async def _handle_messages(self, message: Dict[str, Any]) -> None:
        # Welcoming message, sets the Peer ID linked to a new connection
        if message["type"] == "welcome":
            peer_id = message["peerId"]
            self.peer_id = peer_id
            self.emit("Welcome", peer_id)

        # Notifies listeners that a peer status has changed
        elif message["type"] == "peerStatusChanged":
            roles = message["roles"]
            meta = message["meta"]
            peer_id = message["peerId"]

            self.emit("PeerStatusChanged", peer_id, roles, meta)

        # Instructs a peer to generate an offer and inform about the session ID
        elif message["type"] == "startSession":
            peer_id = message["peerId"]
            session_id = message["sessionId"]
            self.emit("StartSession", peer_id, session_id)

        # Let consumer know that the requested session is starting with the specified identifier
        elif message["type"] == "sessionStarted":
            peer_id = message["peerId"]
            session_id = message["sessionId"]
            self.emit("SessionStarted", peer_id, session_id)

        # Signals that the session the peer was in was ended
        elif message["type"] == "endSession":
            session_id = message["sessionId"]
            self.emit("EndSession", session_id)

        # Messages directly forwarded from one peer to another
        elif message["type"] == "peer":
            session_id = message["sessionId"]
            message = dict(message)
            del message["type"]
            del message["sessionId"]
            self.emit("Peer", session_id, message)

        # Provides the current list of consumer peers
        elif message["type"] == "list":
            producers = message["producers"]
            producers = {p["id"]: p["meta"] for p in producers}
            self.emit("List", producers)

        # Notifies that an error occured with the peer's current session
        elif message["type"] == "error":
            details = message["details"]
            self.logger.error(f'An error occured: "{details}"')
            self.emit("Error", details)

        else:
            self.logger.warning(f"Received unknown message type: {message}.")

    # Messages (peer --> server)
    async def set_peer_status(self, roles: List[str], name: str) -> None:
        """Sets the peer status.

        Args:
            roles (List[str]): List of roles the peer has (producer, listener).
            name (str): Name of the peer.
        """
        if self.peer_id is None:
            raise RuntimeError("PeerId not yet received.")

        for role in roles:
            if role not in ("listener", "producer"):
                raise ValueError(f"Invalid role {role}.")

        message = {
            "type": "setPeerStatus",
            "roles": roles,
            "meta": {"name": name},
            "peerId": self.peer_id,
        }

        await self._send(message)

    async def start_session(self, peer_id: str) -> None:
        """Starts a session with a producer peer.

        Args:
            peer_id (str): Peer ID of the producer peer.
        """
        if self.peer_id is None:
            raise RuntimeError("PeerId not yet received.")

        message = {"type": "startSession", "peerId": peer_id}
        await self._send(message)

    async def end_session(self, session_id: str) -> None:
        """Ends an existing session.

        Args:
            session_id (str): Session ID.
        """
        message = {"type": "endSession", "sessionId": session_id}
        await self._send(message)

    async def send_peer_message(self, session_id: str, type: str, peer_message: Dict[str, Any]) -> None:
        """Sends a message to a peer the sender is currently in session with.

        Args:
            session_id (str): Session ID.
            type (str): Type of the message (sdp or ice).
            peer_message (str): Message to send (sdp or icecandidate).
        """
        message = {
            "type": "peer",
            "sessionId": session_id,
            type: peer_message,
        }

        await self._send(message)

    async def send_list(self) -> None:
        """Requests the current list of producers."""
        message = {"type": "list"}
        await self._send(message)

    async def _send(self, message: Dict[str, Any]) -> None:
        if self.ws is None:
            raise RuntimeError("Not connected.")

        self.logger.debug(f"Sending message: {message}")
        await self.ws.send(json.dumps(message))
