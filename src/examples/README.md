# Examples

## Simple recorder

WebRTC client that records the streams into gdp files, and then mux them into a mp4. Gstreamer rust plugins must be installed. Please follow the [documentation](https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc).

You can directly provide the peer webrtc name (i.e. *robot* for Reachy), or the peer id. Please use --help for more details about the command.

The recorder can be started as follow and will generate a mp4 file.

```shell
python src/examples/recorder/simple_recorder.py --remote-producer-peer-name robot --signaling-host <ip_robot>
```

A Dockerfile is also provided to ease the avoid the compilation of the rust plugins. Navigate to the parent folder of the cloned repo (i.e. `cd ../../..` from this README.md), and build the image

```shell
docker build -t webrtcrecorder -f gst-signalling-py/src/examples/recorder/Dockerfile .
```

Then run the recorder from within a container. Change `~/Videos/`by the path where you want the recording to be saved to.

```shell
docker run --network host -v ~/Videos/:/root/output webrtcrecorder --remote-producer-peer-name robot --signaling-host <ip_robot> --output /root/output/recording.mp4
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