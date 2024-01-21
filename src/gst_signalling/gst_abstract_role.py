import asyncio
import logging
from typing import Any, Dict, NamedTuple, Optional

import gi
import pyee

from .gst_signalling import GstSignalling

gi.require_version("Gst", "1.0")
gi.require_version("GstWebRTC", "1.0")

from gi.repository import Gst

GstSession = NamedTuple(
    "GstSession",
    [
        ("peer_id", str),
        ("pc", Gst.Element),  # type '__gi__.GstWebRTCBin'
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
        self._asyncloop = asyncio.get_event_loop()

        self.sessions: Dict[str, GstSession] = {}

        @signalling.on("Welcome")  # type: ignore[arg-type]
        def on_welcome(peer_id: str) -> None:
            self.peer_id = peer_id
            self.peer_id_evt.set()

        @signalling.on("StartSession")  # type: ignore[arg-type]
        async def on_start_session(peer_id: str, session_id: str) -> None:
            self.logger.info(f"StartSession received, session_id: {session_id}")
            await self.setup_session(session_id, peer_id)

        @signalling.on("SessionStarted")  # type: ignore[arg-type]
        async def on_session_started(peer_id: str, session_id: str) -> None:
            self.logger.info(f"SessionStarted received, session_id: {session_id}")
            await self.setup_session(session_id, peer_id)

        @signalling.on("Peer")  # type: ignore[arg-type]
        async def on_peer(session_id: str, message: Dict[str, Dict[str, Any]]) -> None:
            self.logger.info(
                f"Peer received, session_id: {session_id}, message: {message}"
            )
            await self.peer_for_session(session_id, message)

        @signalling.on("EndSession")  # type: ignore[arg-type]
        async def on_end_session(session_id: str) -> None:
            self.logger.info(f"EndSession received, session_id: {session_id}")
            await self.close_session(session_id)

        self.signalling = signalling

        Gst.init(None)

        self._pipeline = Gst.Pipeline.new()

    def __del__(self) -> None:
        Gst.deinit()

    def make_send_sdp(self, sdp, type: str, session_id: str):  # type: ignore[no-untyped-def]
        self.logger.debug(f"send sdp {type} {sdp}")
        text = sdp.sdp.as_text()
        msg = {"type": type, "sdp": text}
        asyncio.run_coroutine_threadsafe(
            self.send_sdp(session_id, msg), self._asyncloop
        )

    def send_ice_candidate_message(self, _, mlineindex, candidate):  # type: ignore[no-untyped-def]
        icemsg = {"ice": {"candidate": candidate, "sdpMLineIndex": mlineindex}}
        self.logger.debug(icemsg)
        # loop = asyncio.new_event_loop()
        # loop.run_until_complete(self.send_sdp(session_id, icemsg))

    def init_webrtc(self, session_id: str):  # type: ignore[no-untyped-def]
        webrtc = Gst.ElementFactory.make("webrtcbin")
        assert webrtc

        # webrtc.set_property("bundle-policy", "max-bundle")
        # webrtc.set_property("stun-server", "stun://stun.l.google.com:19302")
        # webrtc.set_property(
        #    "turn-server",
        #    "turn://gstreamer:IsGreatWhenYouCanGetItToWork@webrtc.nirbheek.in:3478",
        # )
        webrtc.set_property("stun-server", None)
        webrtc.set_property("turn-server", None)

        # webrtc.connect("on-ice-candidate", lambda *args: self._ices.append(args))
        # webrtc.connect("on-negotiation-needed", self.on_negotiation_needed, session_id)
        webrtc.connect("on-ice-candidate", self.send_ice_candidate_message)
        # webrtc.connect(
        #    "notify::ice-gathering-state", self.on_ice_gathering_state_notify
        # )

        self._pipeline.set_state(Gst.State.READY)
        self._pipeline.add(webrtc)

        return webrtc

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
        self.logger.info("setup session")
        pc = self.init_webrtc(session_id)

        session = GstSession(peer_id, pc)

        self.sessions[session_id] = session

        return session

    async def peer_for_session(
        self, session_id: str, message: Dict[str, Dict[str, str]]
    ) -> None:
        self.logger.info(f"peer for session {session_id} {message}")

    async def close_session(self, session_id: str) -> None:
        self.logger.info("close session")
        """
        session = self.sessions.pop(session_id)

        self.emit("close_session", session)

        await session.pc.close()
        """

    async def send_sdp(self, session_id: str, sdp: Dict[str, Dict[str, str]]) -> None:
        await self.signalling.send_peer_message(session_id, "sdp", sdp)

    async def send_ice(self, session_id: str, ice: Dict[str, Dict[str, str]]) -> None:
        await self.signalling.send_peer_message(session_id, "ice", ice)
