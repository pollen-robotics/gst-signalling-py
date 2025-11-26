import logging
import os
import queue
import threading

import cv2
from aiortc import MediaStreamTrack


# Thread d'affichage OpenCV
class OpenCVDisplayThread(threading.Thread):
    def __init__(self, image_queue):
        super().__init__(daemon=True)
        self.logger = logging.getLogger(__name__)
        self.image_queue = image_queue
        self.running = True

    def run(self):
        self.logger.info("OpenCV display thread started")
        while self.running:
            try:
                img = self.image_queue.get(timeout=0.1)
                # img = np.zeros((400, 400, 3), dtype=np.uint8)
                if img is None:
                    break
                cv2.imshow("frame", img)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.running = False
            except queue.Empty:
                continue
        cv2.destroyAllWindows()


class VideoTrack(MediaStreamTrack):
    display_thread = None
    image_queue = None
    """
    A tactile stream track that feeds a video rendering engine.
    """

    kind = "video"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track
        self.logger = logging.getLogger(__name__)
        self.logger.info("Video track created")
        # Initialise le thread d'affichage une seule fois (pour tous les objets VideoTrack)
        if VideoTrack.image_queue is None:
            VideoTrack.image_queue = queue.Queue(maxsize=2)
            VideoTrack.display_thread = OpenCVDisplayThread(VideoTrack.image_queue)
            VideoTrack.display_thread.start()

        self.output_dir = "frames"
        os.makedirs(self.output_dir, exist_ok=True)

    def stop(self):
        self.logger.info("Video stop")

    async def recv(self):
        frame = await self.track.recv()
        self.logger.debug(f"Video frame: {frame}")
        # Décodage de la frame H264 avec OpenCV
        img = frame.to_ndarray(format="bgr24")
        self.logger.debug(f"Decoded frame shape: {img.shape}")
        # Crée le dossier 'frames' s'il n'existe pas

        # Génère un nom de fichier avec timestamp
        # timestamp = int(time.time() * 1000)
        # filename = os.path.join(self.output_dir, f"frame_{timestamp}.jpg")

        # cv2.imwrite(filename, img)

        # Envoie l'image au thread d'affichage
        try:
            VideoTrack.image_queue.put_nowait(img)
        except queue.Full:
            self.logger.warning("Image queue is full, dropping frame")
        # return frame
