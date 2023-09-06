from collections import namedtuple
import json
from typing import Any, Dict, Optional
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.contrib.signaling import object_from_string, object_to_string
import asyncio
import logging

from .gst_abstract_role import GstSession, GstSignallingAbstractRole


class GstSignallingProducer(GstSignallingAbstractRole):
    def __init__(self, host: str, port: int, name: str, setup_tracks) -> None:
        super().__init__(host, port, setup_tracks)
        self.name = name

    async def connect(self) -> None:
        await super().connect()
        await self.signalling.set_peer_status(roles=["producer"], name=self.name)

    async def setup_session(self, session_id: str, peer_id: str) -> GstSession:
        session = await super().setup_session(session_id, peer_id)

        # send offer
        pc = session.pc
        await pc.setLocalDescription(await pc.createOffer())
        await self.send_sdp(session_id, pc.localDescription)
