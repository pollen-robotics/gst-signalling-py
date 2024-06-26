import logging
from typing import Dict

import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstWebRTC", "1.0")
gi.require_version("GstSdp", "1.0")

from gi.repository import Gst, GstSdp, GstWebRTC  # noqa : E402

from .gst_abstract_role import GstSession, GstSignallingAbstractRole  # noqa : E402


class GstSignallingConsumer(GstSignallingAbstractRole):
    def __init__(
        self,
        host: str,
        port: int,
        producer_peer_id: str,
    ) -> None:
        super().__init__(host, port)
        self.logger = logging.getLogger(__name__)
        self.producer_peer_id = producer_peer_id

    async def connect(self) -> None:
        await super().connect()
        await self.signalling.start_session(self.producer_peer_id)
        self.logger.info("connect")

    async def setup_session(self, session_id: str, peer_id: str) -> GstSession:
        session = await super().setup_session(session_id, peer_id)
        self.logger.info("setup session consumer")

        self._pipeline.set_state(Gst.State.PLAYING)
        self.emit("new_session", session)

        return session

    def on_answer_created(self, promise: Gst.Promise, webrtc: Gst.Element, session_id: str) -> None:
        assert promise.wait() == Gst.PromiseResult.REPLIED
        reply = promise.get_reply()
        # answer = reply["answer"]
        answer = reply.get_value("answer")  # type: ignore[union-attr]
        promise = Gst.Promise.new()
        webrtc.emit("set-local-description", answer, promise)
        promise.interrupt()  # we don't care about the result, discard it
        self.make_send_sdp(answer, "answer", session_id)

    def on_offer_set(self, promise: Gst.Promise, webrtc: Gst.Element, session_id: str) -> None:
        assert promise.wait() == Gst.PromiseResult.REPLIED
        promise = Gst.Promise.new_with_change_func(self.on_answer_created, webrtc, session_id)
        webrtc.emit("create-answer", None, promise)

    async def peer_for_session(self, session_id: str, message: Dict[str, Dict[str, str]]) -> None:
        self.logger.info(f"peer for session {session_id} {message}")

        session = self.sessions[session_id]
        webrtc = session.pc

        if "sdp" in message:
            if message["sdp"]["type"] == "offer":
                _, sdpmsg = GstSdp.SDPMessage.new_from_text(message["sdp"]["sdp"])
                sdp_type = GstWebRTC.WebRTCSDPType.OFFER
                offer = GstWebRTC.WebRTCSessionDescription.new(sdp_type, sdpmsg)
                promise = Gst.Promise.new_with_change_func(self.on_offer_set, webrtc, session_id)
                webrtc.emit("set-remote-description", offer, promise)
                self.logger.debug("set remote desc done")

            elif message["sdp"]["type"] == "answer":
                self.logger.warning("Consumer should not receive the answer")
            else:
                self.logger.error(f"SDP not properly formatted {message['sdp']}")

        elif "ice" in message:
            self.handle_ice_message(webrtc, message["ice"])

        else:
            self.logger.error(f"message not processed {message}")
