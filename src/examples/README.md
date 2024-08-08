# Examples

## Simple recorder

WebRTC client that records the streams into gdp files, and then mux them into a mp4. Gstreamer rust plugins must be installed. Please follow the [documentation](https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc).

You can directly provided the peer webrtc name (i.e. *robot* for Reachy), or the peer id. Please use --help for more details about the command.

The recorder can be started as follow and will generate a mp4 file.

```shell
python src/examples/simple_recorder.py --remote-producer-peer-name robot
```

## Signalling tools

### Listener

The listener simplies print the status of the peer connected to the signalling server

```shell
python src/examples/listener.py 
```

### List of producers

The following commands prints the list of the producers connected to the signalling server

```shell
python src/examples/get_producer_list.py
```