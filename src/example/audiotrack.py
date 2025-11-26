import logging

from aiortc import MediaStreamTrack


class AudioTrack(MediaStreamTrack):
    """
    A tactile stream track that feeds a audio rendering engine.
    """

    kind = "audio"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track
        self.logger = logging.getLogger(__name__)
        self.logger.info("Audio track created")

    def stop(self):
        self.logger.info("Audio stop")

    async def recv(self):
        frame = await self.track.recv()
        self.logger.debug(f"Audio frame: {frame}")
        """
        if self.first_start:
            self.first_start = False
            device_id = 15# GetDefaultDeviceID()
            if device_id == -1:
                self.logger.error("Audio device not found")
            else:
                self.logger.info("Start renderer")
                if frame.format.name != "s16":
                    self.logger.warning("audio sample format not supported")
                self.audioR.run(
                    sampling_rate=frame.rate, device_id=device_id, blocksize=frame.samples, dtype='s16')
        data = frame.to_ndarray(format="s16")
        if frame.format.is_planar is False:
            data = data.reshape((frame.samples, 2))  # len(data) == samples * 2
            # data = np.array([data[:, 0], data[:, 1]])
            self.audioR.fill_data(data)
        else:
            self.logger.warning("Planar data not supported")
    """
