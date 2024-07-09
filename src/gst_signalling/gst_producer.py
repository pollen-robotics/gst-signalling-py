import logging
from typing import Dict

from gi.repository import Gst, GstSdp, GstWebRTC

from .gst_abstract_role import GstSession, GstSignallingAbstractRole


class GstSignallingProducer(GstSignallingAbstractRole):
    def __init__(self, host: str, port: int, name: str) -> None:
        super().__init__(host, port)
        self.name = name
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> None:
        await super().connect()
        await self.signalling.set_peer_status(roles=["producer"], name=self.name)

    async def serve4ever(self) -> None:
        await self.connect()
        await self.consume()

    def on_offer_created(self, promise: Gst.Promise, webrtc: Gst.Element, session_id: str) -> None:
        self.logger.debug(f"on offer created {promise} {webrtc} {session_id}")
        assert promise.wait() == Gst.PromiseResult.REPLIED
        reply = promise.get_reply()
        offer = reply.get_value("offer")  # type: ignore[union-attr]

        promise = Gst.Promise.new()
        self.logger.info("Offer created, setting local description")
        webrtc.emit("set-local-description", offer, promise)
        promise.interrupt()
        self.make_send_sdp(offer, "offer", session_id)

    def on_negotiation_needed(self, element: Gst.Element, session_id: str) -> None:
        self.logger.debug(f"on negociation needed {element} {session_id}")
        promise = Gst.Promise.new_with_change_func(self.on_offer_created, element, session_id)
        element.emit("create-offer", None, promise)

    async def setup_session(self, session_id: str, peer_id: str) -> GstSession:
        session = await super().setup_session(session_id, peer_id)
        self.logger.info("setup session producer")

        # send offer
        pc = session.pc
        pc.connect("on-negotiation-needed", self.on_negotiation_needed, session_id)

        pc.sync_state_with_parent()
        self.emit("new_session", session)

        return session

    async def peer_for_session(self, session_id: str, message: Dict[str, Dict[str, str]]) -> None:
        self.logger.info(f"peer for session {session_id} {message}")

        session = self.sessions[session_id]
        webrtc = session.pc

        if "sdp" in message:
            if message["sdp"]["type"] == "answer":
                self.logger.debug("set remote desc")
                _, sdpmsg = GstSdp.SDPMessage.new_from_text(message["sdp"]["sdp"])

                sdp_type = GstWebRTC.WebRTCSDPType.ANSWER
                answer = GstWebRTC.WebRTCSessionDescription.new(sdp_type, sdpmsg)

                promise = Gst.Promise.new()
                webrtc.emit("set-remote-description", answer, promise)
                promise.interrupt()
                self.logger.debug("set remote desc done")
            elif message["sdp"]["type"] == "offer":
                self.logger.warning("producer should not receive the offer")
            else:
                self.logger.error(f"SDP not properly formatted {message['sdp']}")
        elif "ice" in message:
            self.handle_ice_message(webrtc, message["ice"])
        else:
            self.logger.error(f"message not processed {message}")
