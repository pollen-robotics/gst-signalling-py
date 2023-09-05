Data channel CLI
================

This example illustrates the establishment of a data channel using an
RTCPeerConnection and the gstreamer signaling channel to exchange SDP.

First, run the gtreamer signaling server (see https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc for details). 

.. code-block:: console

   $ WEBRTCSINK_SIGNALLING_SERVER_LOG=info gst-webrtc-signalling-server


To run the example, you will need instances of the `cli` example:

- The first takes on the role of the producer and sets its name to `datachannel-cli-producer`.

.. code-block:: console

   $ python cli.py producer --name datachannel-cli-producer

- The second takes on the role of the consumer and uses the producer name to find it. 

.. code-block:: console

   $ python cli.py consumer --remote-producer-peer-name datachannel-cli-producer


You can also use peer_id instead of peer_name.
