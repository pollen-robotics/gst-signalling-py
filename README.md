# Python implementation of the gstreamer WebRTC signalling protocol

Please refer to the gstreamer documentation, for more information on the signalling protocol.
https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc

This repository provides a low-level API close to the gstreamer API, and a higher-level API matching the great [aiortc](https://github.com/aiortc/aiortc) library.
The examples given here, are directly taken from aiortc with only minor modifications to adapt to the gstreamer signalling.

_Please note that while most WebRTC libraries use the word signaling, the gstreamer implementation use singalling. This repository uses both trying to match closely to the used APIs._


## Contribute

Please refer to our [template repository](https://github.com/pollen-robotics/python-template) for guidlines and coding style.