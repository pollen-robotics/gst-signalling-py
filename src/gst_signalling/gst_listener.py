import asyncio
from typing import Dict, List

from .gst_abstract_role import GstSignallingAbstractRole


class GstSignallingListener(GstSignallingAbstractRole):
    def __init__(self, host: str, port: int, name: str) -> None:
        GstSignallingAbstractRole.__init__(self, host=host, port=port)
        self.name = name

        @self.signalling.on("PeerStatusChanged")
        def on_peer_status_changed(
            peer_id: str,
            roles: List[str],
            meta: Dict[str, str],
        ) -> None:
            self.emit("PeerStatusChanged", peer_id, roles, meta)

    async def connect(self) -> None:
        await super().connect()
        await self.signalling.set_peer_status(roles=["listener"], name=self.name)

    async def serve4ever(self) -> None:
        await self.connect()
        await self.consume()

    async def consume(self) -> None:
        while True:
            await asyncio.sleep(1)

    async def close(self) -> None:
        await self.signalling.close()
