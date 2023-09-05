Video channel CLI
=================

This example illustrates the establishment of a video stream using an
RTCPeerConnection.

It uses the gstreamer signaling mecanisms.

By default the sent video is an animated French flag, but it is also possible
to use a MediaPlayer to read media from a file.

This example also illustrates how to use a MediaRecorder to capture media to a
file.

Running the example
-------------------

First, run the gtreamer signaling server (see https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc for details). 

.. code-block:: console

   $ WEBRTCSINK_SIGNALLING_SERVER_LOG=info gst-webrtc-signalling-server

To run the example, you will need instances of the `cli` example:

- The first takes on the role of the producer and sets its name to
  `videostream-cli-producer`.

.. code-block:: console

   $ python cli.py producer --name videostream-cli-producer

- The second takes on the role of the consumer.

.. code-block:: console

   $ python cli.py consumer --remote-producer-peer-name videostream-cli-producer

Additional options
------------------

If you want to play a media file instead of sending the example image, run:

.. code-block:: console

   $ python cli.py --play-from video.mp4

If you want to recording the received video you can run one of the following:

.. code-block:: console

   $ python cli.py answer --record-to video.mp4
   $ python cli.py answer --record-to video-%3d.png
