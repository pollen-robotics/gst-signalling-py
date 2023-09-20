# GStreamer Consumer

Playback an audiovideo stream from a [webrtc producer](https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc). Basically it encapsulates the *gst-launch-1.0 playbin uri=gstwebrtc* example.

## Requirements

```console
pip install PyGObject
```

Don't forget to configure gstreamer plugins path

``` console
export GST_PLUGIN_PATH=<path/target/debug:$GST_PLUGIN_PATH
```

## Usage

Playing AV content from gstreamer example producer

```console
python src/example/gstreamer_consumer/gstreamer_consumer.py --producer-name gst-stream -v
```
