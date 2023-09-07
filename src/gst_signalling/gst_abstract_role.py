from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.contrib.signaling import object_from_string, object_to_string
import asyncio
import json
import logging
import pyee
from typing import Any, Dict, NamedTuple, Optional


from .gst_signalling import GstSignalling


GstSession = NamedTuple(
    "GstSession",
    [
        ("peer_id", str),
        ("pc", RTCPeerConnection),
    ],
)


class GstSignallingAbstractRole(pyee.AsyncIOEventEmitter):
    def __init__(
        self,
        host: str,
        port: int,
    ) -> None:
        pyee.AsyncIOEventEmitter.__init__(self)  # type: ignore[no-untyped-call]

        self.logger = logging.getLogger(__name__)

        signalling = GstSignalling(host=host, port=port)

        self.peer_id: Optional[str] = None
        self.peer_id_evt = asyncio.Event()

        self.sessions: Dict[str, GstSession] = {}

        @signalling.on("Welcome")
        def on_welcome(peer_id: str) -> None:
            self.peer_id = peer_id
            self.peer_id_evt.set()

        @signalling.on("StartSession")
        async def on_start_session(peer_id: str, session_id: str) -> None:
            self.logger.info(f"StartSession received, session_id: {session_id}")
            await self.setup_session(session_id, peer_id)

        @signalling.on("SessionStarted")
        async def on_session_started(peer_id: str, session_id: str) -> None:
            self.logger.info(f"SessionStarted received, session_id: {session_id}")
            await self.setup_session(session_id, peer_id)

        @signalling.on("Peer")
        async def on_peer(session_id: str, message: Dict[str, Dict[str, Any]]) -> None:
            self.logger.info(
                f"Peer received, session_id: {session_id}, message: {message}"
            )
            await self.peer_for_session(session_id, message)

        @signalling.on("EndSession")
        async def on_end_session(session_id: str) -> None:
            self.logger.info(f"EndSession received, session_id: {session_id}")
            await self.close_session(session_id)

        self.signalling = signalling

    async def connect(self) -> None:
        assert self.signalling is not None

        await self.signalling.connect()
        await self.peer_id_evt.wait()

    async def close(self) -> None:
        await self.signalling.close()

    async def consume(self) -> None:
        while True:
            await asyncio.sleep(1000)

    # Session management
    async def setup_session(self, session_id: str, peer_id: str) -> GstSession:
        pc = RTCPeerConnection()

        session = GstSession(peer_id, pc)
        self.sessions[session_id] = session

        self.emit("new_session", session)

        return session

    async def peer_for_session(
        self, session_id: str, message: Dict[str, Dict[str, Any]]
    ) -> None:
        session = self.sessions[session_id]
        pc = session.pc

        if "sdp" in message:
            obj = object_from_string(json.dumps(message["sdp"]))

            if isinstance(obj, RTCSessionDescription):
                if obj.type == "offer":
                    self.logger.info("Received offer sdp")
                    await pc.setRemoteDescription(obj)

                    self.logger.info("Sending answer")
                    await pc.setLocalDescription(await pc.createAnswer())

                    self.logger.info("Sending answer sdp")
                    await self.send_sdp(session_id, pc.localDescription)

                elif obj.type == "answer":
                    self.logger.info("Received answer sdp")
                    await pc.setRemoteDescription(obj)

        elif "ice" in message:
            obj = object_from_string(json.dumps(message["ice"]))
            if isinstance(obj, RTCIceCandidate):
                self.logger.info("Received ice candidate")
                pc.addIceCandidate(obj)

    async def close_session(self, session_id: str) -> None:
        session = self.sessions.pop(session_id)

        self.emit("close_session", session)

        await session.pc.close()

    async def send_sdp(self, session_id: str, sdp: RTCSessionDescription) -> None:
        await self.signalling.send_peer_message(
            session_id, "sdp", json.loads(object_to_string(sdp))
        )
