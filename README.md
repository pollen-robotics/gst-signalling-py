# gst-signalling-py: Gstreamer WebRTC signalling in Python

This repository provides a Python implementation of the [Gstreamer WebRTC signalling](https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc) protocol. 

* It provides an API close to the gstreamer API with a [producer](./src/gst_signalling/gst_producer.py) and a [consumer](./src/gst_signalling/gst_consumer.py). This allows to simply write producer/consumer examples using gstreamer signalling. It works with single producer and multiple consumers. See the [data producer example](./src/example/datachannel-single-producer-multiple-consumer/) for more details.
* And an API matching the signaling examples from the [aiortc](https://github.com/aiortc/aiortc) library. Some of the examples given here, are directly taken from aiortc with only minor modifications to adapt to the specifity of the gstreamer signalling. They could be a good starting point to understand how to use this library with aiortc.

_Please note that while most WebRTC libraries use the word signaling, the gstreamer implementation use singalling. This repository uses both trying to match closely to the used APIs._

### Features 

- [x] Producer and consumer support
- [ ] Listener
- [x] Examples
    - [x] Integration with aiortc
    - [x] Integration with gstreamer

## Installation

Simply install the package using pip:

```bash
pip install -e .
```

## Usage

See the examples for more details.

## Protocol

### Roles

Gstreamer signalling defines 3 roles (so the WebRTC peers are not symmetrical)

- producer (produces data, video or audio streams)
- consumer (access to a producer stream, can access all or a subset of its streams)
- listener (gets notified by the server of new producers status)

### Protocol sequence diagram

```mermaid
sequenceDiagram
  Server-->>Producer: Welcome (PeerId)
	Server-->>Consumer: Welcome (PeerId)
  Producer->>Server: PeerStatusChanged  # declare yourself as producer
	Consumer->>Server: StartSession # with producer PeerId
	Server-->>Producer: StartSession (SessionId)
	Server-->>Consumer: SessionStarted (SessionId)
	Producer->>Server: Peer (offer sdp)
	Server-->>Consumer: Peer (offer sdp)
	Consumer->>Server: Peer (answer sdp)
	Server-->>Producer: Peer (answer sdp)
```

See [this page](https://pollen-robotics.notion.site/Gstreamer-WebRTC-signaling-8cc2391ef0004ef6b399095ea507121f?pvs=4) for more details.


## Contribute

Please refer to our [template repository](https://github.com/pollen-robotics/python-template) for guidlines and coding style.