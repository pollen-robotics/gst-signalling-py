from .gst_abstract_role import GstSession, GstSignallingAbstractRole


class GstSignallingProducer(GstSignallingAbstractRole):
    def __init__(
        self,
        host: str,
        port: int,
        name: str,
    ) -> None:
        super().__init__(host, port)
        self.name = name

    async def connect(self) -> None:
        await super().connect()
        await self.signalling.set_peer_status(roles=["producer"], name=self.name)

    async def serve4ever(self) -> None:
        await self.connect()
        await self.consume()

    async def setup_session(self, session_id: str, peer_id: str) -> GstSession:
        session = await super().setup_session(session_id, peer_id)

        # send offer
        pc = session.pc
        await pc.setLocalDescription(await pc.createOffer())
        await self.send_sdp(session_id, pc.localDescription)

        return session
