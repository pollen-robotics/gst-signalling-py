from .gst_abstract_role import GstSignallingAbstractRole


class GstSignallingConsumer(GstSignallingAbstractRole):
    def __init__(
        self,
        host: str,
        port: int,
        producer_peer_id: str,
    ) -> None:
        super().__init__(host, port)
        self.producer_peer_id = producer_peer_id

    async def connect(self) -> None:
        await super().connect()
        await self.signalling.start_session(self.producer_peer_id)
