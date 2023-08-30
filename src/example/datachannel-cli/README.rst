Data channel CLI
================

This example illustrates the establishment of a data channel using an
RTCPeerConnection and the gstreamer signaling channel to exchange SDP.

First, run the gtreamer signaling server (see https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc for details). 

.. code-block:: console

   $ WEBRTCSINK_SIGNALLING_SERVER_LOG=info gst-webrtc-signalling-server


To run the example, you will need instances of the `cli` example:

- The first takes on the role of the producer. It will show its PeerId that you will need to copy paste to the second instance.

.. code-block:: console

   $ python cli.py producer -v

- The second takes on the role of the consumer. 

.. code-block:: console

   $ python cli.py consumer -v --remote-producer-peer-id <producer-peer-id>
