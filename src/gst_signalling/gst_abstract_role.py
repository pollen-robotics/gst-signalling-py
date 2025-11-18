import asyncio
import logging
from typing import Any, Dict, NamedTuple, Optional

import gi
from pyee.asyncio import AsyncIOEventEmitter

from .gst_signalling import GstSignalling

gi.require_version("Gst", "1.0")
gi.require_version("GstWebRTC", "1.0")

from gi.repository import Gst  # noqa : E402

GstSession = NamedTuple(
    "GstSession",
    [
        ("peer_id", str),
        ("session_id", str),
        ("pc", Gst.Element),  # type '__gi__.GstWebRTCBin'
    ],
)


class GstSignallingAbstractRole(AsyncIOEventEmitter):
    def __init__(
        self,
        host: str,
        port: int,
    ) -> None:
        super().__init__()

        self.logger = logging.getLogger(__name__)

        signalling = GstSignalling(host=host, port=port)

        self.peer_id: Optional[str] = None
        self.peer_id_evt = asyncio.Event()
        self.consume_evt = asyncio.Event()
        self._asyncloop = asyncio.get_event_loop()

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
            self.logger.info(f"Peer received, session_id: {session_id}, message: {message}")
            await self.peer_for_session(session_id, message)

        @signalling.on("EndSession")
        async def on_end_session(session_id: str) -> None:
            self.logger.info(f"EndSession received, session_id: {session_id}")
            await self.close_session(session_id)

        self.signalling = signalling

        Gst.init(None)

        self._pipeline = Gst.Pipeline.new()
        # pipeline will only contain dynamically added webrtcbins
        self._pipeline.set_state(Gst.State.PLAYING)

    def __del__(self) -> None:
        self._pipeline.set_state(Gst.State.NULL)
        # Gst.deinit()

    def make_send_sdp(self, sdp: Any, type: str, session_id: str) -> None:  # sdp is GstWebRTC.WebRTCSessionDescription
        text = sdp.sdp.as_text()
        msg = {"type": type, "sdp": text}
        asyncio.run_coroutine_threadsafe(self.send_sdp(session_id, msg), self._asyncloop)

    def send_ice_candidate_message(self, _: Gst.Element, mlineindex: int, candidate: str, session_id: str) -> None:
        icemsg = {"candidate": candidate, "sdpMLineIndex": mlineindex}
        asyncio.run_coroutine_threadsafe(self.send_ice(session_id, icemsg), self._asyncloop)

    def init_webrtc(self, session_id: str) -> Gst.Element:
        webrtc = Gst.ElementFactory.make("webrtcbin")
        assert webrtc

        webrtc.set_property("bundle-policy", "max-bundle")
        webrtc.connect("on-ice-candidate", self.send_ice_candidate_message, session_id)

        self._pipeline.add(webrtc)

        return webrtc

    async def connect(self) -> None:
        assert self.signalling is not None

        await self.signalling.connect()
        await self.peer_id_evt.wait()

    async def close(self) -> None:
        await self.signalling.close()
        self.consume_evt.set()

    async def consume(self) -> None:
        # while True:
        #    await asyncio.sleep(1000)
        await self.consume_evt.wait()

    # Session management
    async def setup_session(self, session_id: str, peer_id: str) -> GstSession:
        self.logger.info("setup session")
        pc = self.init_webrtc(session_id)

        session = GstSession(peer_id, session_id, pc)

        self.sessions[session_id] = session

        return session

    async def peer_for_session(self, session_id: str, message: Dict[str, Dict[str, str]]) -> None:
        self.logger.info(f"peer for session {session_id} {message}")

    def handle_ice_message(self, webrtc: Gst.Element, ice_msg: Dict[str, Any]) -> None:
        candidate = ice_msg["candidate"]
        sdpmlineindex = ice_msg["sdpMLineIndex"]
        webrtc.emit("add-ice-candidate", sdpmlineindex, candidate)

    async def close_session(self, session_id: str) -> None:
        self.logger.info("close session")
        try:
            session = self.sessions.pop(session_id)
            self._pipeline.remove(session.pc)
            session.pc.set_state(Gst.State.NULL)
            await self.signalling.end_session(session_id)
            # self.emit("close_session", session)
        except KeyError:
            self.logger.warning("Session not found")

    async def send_sdp(self, session_id: str, sdp: Dict[str, Dict[str, str]]) -> None:
        await self.signalling.send_peer_message(session_id, "sdp", sdp)

    async def send_ice(self, session_id: str, ice: Dict[str, Any]) -> None:
        await self.signalling.send_peer_message(session_id, "ice", ice)
